"""Stream adapters to interface chunk generators with standard Python I/O."""

import io
from typing import Generator, Iterator


class ChunkGeneratorReader(io.RawIOBase):
    """An io.RawIOBase stream adapter that reads from a generator of byte chunks.

    Allows incremental streaming into io.TextIOWrapper and csv.reader with O(chunk_size) memory.
    """

    def __init__(self, chunk_generator: Iterator[bytes]):
        super().__init__()
        self._gen = chunk_generator
        self._buffer = bytearray()
        self._eof = False
        self.total_bytes_read = 0

    def readable(self) -> bool:
        return True

    def readinto(self, b) -> int:
        """Read bytes into buffer b without unbounded accumulation."""
        while len(self._buffer) < len(b) and not self._eof:
            try:
                next_chunk = next(self._gen)
                if next_chunk:
                    self._buffer.extend(next_chunk)
            except StopIteration:
                self._eof = True
                break

        if not self._buffer and self._eof:
            return 0

        num_bytes = min(len(b), len(self._buffer))
        b[:num_bytes] = self._buffer[:num_bytes]
        del self._buffer[:num_bytes]
        self.total_bytes_read += num_bytes
        return num_bytes

