"""Incremental decompressed-stream SHA-256 calculation."""

import hashlib
from typing import Iterator


class StreamHasher:
    """Computes SHA-256 over an uncompressed byte stream on the fly."""

    def __init__(self):
        self._hasher = hashlib.sha256()
        self.total_bytes = 0

    def update(self, chunk: bytes) -> None:
        """Feed uncompressed bytes into the running digest."""
        if chunk:
            self._hasher.update(chunk)
            self.total_bytes += len(chunk)

    def hexdigest(self) -> str:
        """Return final SHA-256 hex digest."""
        return self._hasher.hexdigest()


def compute_stream_sha256(chunk_iterator: Iterator[bytes]) -> str:
    """Convenience helper to compute SHA-256 of all chunks in an iterator."""
    hasher = StreamHasher()
    for chunk in chunk_iterator:
        hasher.update(chunk)
    return hasher.hexdigest()

