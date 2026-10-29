"""Compression format detection helpers and signatures."""

from dbguard.file_inspector import detect_compression_format, MAGIC_GZIP, MAGIC_BZIP2, MAGIC_XZ, MAGIC_ZSTD
from dbguard.models import CompressionFormat

__all__ = ["detect_compression_format", "MAGIC_GZIP", "MAGIC_BZIP2", "MAGIC_XZ", "MAGIC_ZSTD", "CompressionFormat"]

