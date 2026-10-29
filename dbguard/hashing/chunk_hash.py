"""Fixed-size byte chunk hashing for granular stream integrity."""

import hashlib
from typing import Iterator, List
from dbguard.models import ChunkHashEntry

DEFAULT_CHUNK_VERIFY_SIZE = 1_048_576  # 1 MB chunk boundaries


class ChunkHasher:
    """Partitions an uncompressed byte stream into exact fixed-size byte chunks and hashes each chunk."""

    def __init__(self, chunk_boundary_bytes: int = DEFAULT_CHUNK_VERIFY_SIZE):
        self.chunk_boundary_bytes = chunk_boundary_bytes
        self.entries: List[ChunkHashEntry] = []
        self._current_chunk_hasher = hashlib.sha256()
        self._current_chunk_bytes = 0
        self._total_bytes = 0
        self._chunk_index = 0

    def update(self, data: bytes) -> None:
        """Feed bytes and finalize chunk entries whenever the boundary is reached."""
        offset = 0
        while offset < len(data):
            needed = self.chunk_boundary_bytes - self._current_chunk_bytes
            slice_bytes = data[offset:offset + needed]
            self._current_chunk_hasher.update(slice_bytes)
            self._current_chunk_bytes += len(slice_bytes)
            self._total_bytes += len(slice_bytes)
            offset += len(slice_bytes)

            if self._current_chunk_bytes == self.chunk_boundary_bytes:
                self._finalize_current_chunk()

    def _finalize_current_chunk(self) -> None:
        start_byte = self._total_bytes - self._current_chunk_bytes
        end_byte = self._total_bytes
        sha256_digest = self._current_chunk_hasher.hexdigest()

        self.entries.append(ChunkHashEntry(
            index=self._chunk_index,
            start_byte=start_byte,
            end_byte=end_byte,
            length_bytes=self._current_chunk_bytes,
            sha256=sha256_digest,
            record_count=None
        ))
        self._chunk_index += 1
        self._current_chunk_hasher = hashlib.sha256()
        self._current_chunk_bytes = 0

    def finalize(self) -> List[ChunkHashEntry]:
        """Finalize any remaining trailing bytes in the last chunk."""
        if self._current_chunk_bytes > 0:
            self._finalize_current_chunk()
        return self.entries

