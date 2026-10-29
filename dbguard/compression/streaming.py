"""Module 2: Streaming Compression Engine.

Provides an incremental, bounded-memory decompression abstraction across
GZIP, BZIP2, XZ, and Zstandard formats. Enforces expansion-ratio and
decompressed-size limits to protect against compression bombs.
"""

import bz2
import gzip
import io
import lzma
import os
import zlib
from pathlib import Path
from typing import BinaryIO, Generator, Optional, Tuple, Union

from dbguard.exceptions import (
    CompressionError,
    CorruptedStreamError,
    ResourceLimitExceededError,
    TruncatedStreamError,
    UnsupportedFormatError,
)
from dbguard.models import CompressionFormat

try:
    import zstandard as zstd
    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False

DEFAULT_BUFFER_SIZE = 65_536  # 64 KB read buffer
DEFAULT_MAX_DECOMPRESSED_SIZE = 5_368_709_120  # 5 GB safety limit
DEFAULT_MAX_EXPANSION_RATIO = 100.0  # Alert/stop if decompressed > 100x compressed


class StreamingDecompressor:
    """Incremental, bounded-memory decompressor for multiple compression formats."""

    def __init__(
        self,
        stream_or_path: Union[str, Path, BinaryIO],
        format_type: CompressionFormat,
        chunk_size: int = DEFAULT_BUFFER_SIZE,
        max_decompressed_size: int = DEFAULT_MAX_DECOMPRESSED_SIZE,
        max_expansion_ratio: float = DEFAULT_MAX_EXPANSION_RATIO,
    ):
        self.stream_or_path = stream_or_path
        self.format_type = format_type
        self.chunk_size = chunk_size
        self.max_decompressed_size = max_decompressed_size
        self.max_expansion_ratio = max_expansion_ratio

        self.compressed_bytes_read = 0
        self.decompressed_bytes_written = 0
        self._raw_file: Optional[BinaryIO] = None
        self._owns_file = False

    def _open_raw(self) -> BinaryIO:
        if isinstance(self.stream_or_path, (str, Path)):
            self._owns_file = True
            return open(self.stream_or_path, "rb")
        else:
            self._owns_file = False
            if hasattr(self.stream_or_path, "seek"):
                self.stream_or_path.seek(0)
            return self.stream_or_path

    def stream_chunks(self) -> Generator[bytes, None, None]:
        """Yield uncompressed byte chunks while tracking byte counts and checking safety limits."""
        self._raw_file = self._open_raw()
        self.compressed_bytes_read = 0
        self.decompressed_bytes_written = 0

        try:
            if self.format_type == CompressionFormat.GZIP:
                yield from self._stream_gzip()
            elif self.format_type == CompressionFormat.BZIP2:
                yield from self._stream_bz2()
            elif self.format_type == CompressionFormat.XZ:
                yield from self._stream_xz()
            elif self.format_type == CompressionFormat.ZSTD:
                yield from self._stream_zstd()
            elif self.format_type == CompressionFormat.UNCOMPRESSED:
                yield from self._stream_uncompressed()
            else:
                raise UnsupportedFormatError(f"Unsupported compression format: {self.format_type}")
        finally:
            if self._owns_file and self._raw_file:
                self._raw_file.close()

    def _check_safety_limits(self, new_chunk_len: int) -> None:
        """Enforce decompressed byte caps and expansion ratio thresholds."""
        self.decompressed_bytes_written += new_chunk_len

        if self.decompressed_bytes_written > self.max_decompressed_size:
            raise ResourceLimitExceededError(
                f"Decompressed output ({self.decompressed_bytes_written:,} bytes) exceeded safety limit of "
                f"{self.max_decompressed_size:,} bytes."
            )

        # Only check ratio once we have a meaningful sample (> 512 KB uncompressed)
        if self.decompressed_bytes_written > 524_288:
            ratio = self.decompressed_bytes_written / max(1, self.compressed_bytes_read)
            if ratio > self.max_expansion_ratio:
                raise ResourceLimitExceededError(
                    f"Expansion ratio {ratio:.1f}x exceeded safety ceiling of {self.max_expansion_ratio:.1f}x."
                )

    def _stream_gzip(self) -> Generator[bytes, None, None]:
        """Stream gzip handling multi-member archives and verifying CRC-32."""
        # Using gzip.GzipFile ensures trailer CRC and uncompressed ISIZE verification
        try:
            gz = gzip.GzipFile(fileobj=self._raw_file, mode="rb")
            while True:
                # Track raw file position to determine compressed bytes read
                pos_before = self._raw_file.tell() if hasattr(self._raw_file, "tell") else 0
                chunk = gz.read(self.chunk_size)
                pos_after = self._raw_file.tell() if hasattr(self._raw_file, "tell") else 0
                if pos_after >= pos_before:
                    self.compressed_bytes_read += (pos_after - pos_before)

                if not chunk:
                    # Check whether GzipFile verified the trailer
                    break

                self._check_safety_limits(len(chunk))
                yield chunk

        except (gzip.BadGzipFile, zlib.error) as e:
            raise CorruptedStreamError(f"GZIP stream corrupted: {e}") from e
        except EOFError as e:
            raise TruncatedStreamError(f"GZIP stream truncated before end-of-member marker: {e}") from e

    def _stream_bz2(self) -> Generator[bytes, None, None]:
        """Stream bzip2 decompressed blocks incrementally."""
        decompressor = bz2.BZ2Decompressor()
        eof_reached = False

        while True:
            raw_chunk = self._raw_file.read(self.chunk_size)
            if not raw_chunk:
                break

            self.compressed_bytes_read += len(raw_chunk)
            try:
                out = decompressor.decompress(raw_chunk)
                if out:
                    self._check_safety_limits(len(out))
                    yield out
                if decompressor.eof:
                    eof_reached = True
                    # Check for trailing concatenated streams or finish
                    if decompressor.unused_data:
                        decompressor = bz2.BZ2Decompressor()
                        out2 = decompressor.decompress(decompressor.unused_data)
                        if out2:
                            self._check_safety_limits(len(out2))
                            yield out2
            except OSError as e:
                raise CorruptedStreamError(f"BZIP2 payload corrupted: {e}") from e

        if not eof_reached and self.compressed_bytes_read > 0:
            raise TruncatedStreamError("BZIP2 stream ended abruptly without final stream terminator.")

    def _stream_xz(self) -> Generator[bytes, None, None]:
        """Stream XZ (LZMA) decompressed blocks incrementally."""
        decompressor = lzma.LZMADecompressor()
        eof_reached = False

        while True:
            raw_chunk = self._raw_file.read(self.chunk_size)
            if not raw_chunk:
                break

            self.compressed_bytes_read += len(raw_chunk)
            try:
                out = decompressor.decompress(raw_chunk)
                if out:
                    self._check_safety_limits(len(out))
                    yield out
                if decompressor.eof:
                    eof_reached = True
                    if decompressor.unused_data:
                        decompressor = lzma.LZMADecompressor()
                        out2 = decompressor.decompress(decompressor.unused_data)
                        if out2:
                            self._check_safety_limits(len(out2))
                            yield out2
            except lzma.LZMAError as e:
                raise CorruptedStreamError(f"XZ/LZMA stream corrupted: {e}") from e

        if not eof_reached and self.compressed_bytes_read > 0:
            raise TruncatedStreamError("XZ stream truncated unexpectedly.")

    def _stream_zstd(self) -> Generator[bytes, None, None]:
        """Stream Zstandard decompressed frames incrementally."""
        if not HAS_ZSTD:
            raise UnsupportedFormatError("zstandard package is required to decompress ZSTD exports.")

        dctx = zstd.ZstdDecompressor()
        reader = dctx.stream_reader(self._raw_file)
        try:
            while True:
                pos_before = self._raw_file.tell() if hasattr(self._raw_file, "tell") else 0
                chunk = reader.read(self.chunk_size)
                pos_after = self._raw_file.tell() if hasattr(self._raw_file, "tell") else 0
                if pos_after >= pos_before:
                    self.compressed_bytes_read += (pos_after - pos_before)

                if not chunk:
                    break

                self._check_safety_limits(len(chunk))
                yield chunk
        except zstd.ZstdError as e:
            raise CorruptedStreamError(f"Zstandard stream corrupted or truncated: {e}") from e

    def _stream_uncompressed(self) -> Generator[bytes, None, None]:
        """Stream uncompressed raw text bytes."""
        while True:
            chunk = self._raw_file.read(self.chunk_size)
            if not chunk:
                break
            self.compressed_bytes_read += len(chunk)
            self._check_safety_limits(len(chunk))
            yield chunk

