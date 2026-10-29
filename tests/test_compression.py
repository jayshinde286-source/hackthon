"""Tests for Module 2 & 3: Compression Streaming and Integrity Validation."""

import gzip
import io
import os
import pytest
from pathlib import Path

from dbguard.compression.detector import detect_compression_format
from dbguard.compression.integrity import validate_compression_integrity
from dbguard.compression.streaming import StreamingDecompressor
from dbguard.exceptions import (
    CorruptedStreamError,
    ResourceLimitExceededError,
    TruncatedStreamError,
    UnsupportedFormatError,
)
from dbguard.models import CompressionFormat, VerificationStatus


def test_valid_gzip(tmp_path: Path):
    """Test 1: Valid gzip file decompresses cleanly and passes integrity validation."""
    data = b"col1,col2,col3\n1,foo,100\n2,bar,200\n"
    gz_path = tmp_path / "valid.csv.gz"
    with gzip.open(gz_path, "wb") as f:
        f.write(data)

    res = validate_compression_integrity(gz_path, CompressionFormat.GZIP)
    assert res.status == VerificationStatus.PASS
    assert res.decompressed_bytes == len(data)
    assert res.crc_or_trailer_valid is True
    assert not res.is_truncated


def test_invalid_gzip_header(tmp_path: Path):
    """Test 2: Non-gzip header signature is detected as UNKNOWN or rejected."""
    bad_path = tmp_path / "bad_header.csv.gz"
    bad_path.write_bytes(b"NOT_A_GZIP_FILE_AT_ALL_JUST_JUNK")

    fmt = detect_compression_format(bad_path.read_bytes()[:16])
    assert fmt != CompressionFormat.GZIP


def test_truncated_gzip(tmp_path: Path):
    """Test 3: Truncated gzip stream raises error and reports FAIL with is_truncated=True."""
    data = b"a" * 100_000
    gz_buf = io.BytesIO()
    with gzip.GzipFile(fileobj=gz_buf, mode="wb") as f:
        f.write(data)
    full_bytes = gz_buf.getvalue()

    # Truncate at half without trailer
    truncated_path = tmp_path / "truncated.gz"
    truncated_path.write_bytes(full_bytes[: len(full_bytes) // 2])

    res = validate_compression_integrity(truncated_path, CompressionFormat.GZIP)
    assert res.status == VerificationStatus.FAIL
    assert res.is_truncated is True
    assert res.crc_or_trailer_valid is False


def test_corrupted_payload(tmp_path: Path):
    """Test 4: Mutated payload bytes in gzip stream are detected as corrupted."""
    data = b"Some sensible data that compresses into multiple blocks " * 1000
    gz_buf = io.BytesIO()
    with gzip.GzipFile(fileobj=gz_buf, mode="wb") as f:
        f.write(data)
    raw = bytearray(gz_buf.getvalue())

    # Mutate byte in the middle of DEFLATE stream
    raw[len(raw) // 2] ^= 0xFF

    corrupt_path = tmp_path / "corrupt.gz"
    corrupt_path.write_bytes(raw)

    res = validate_compression_integrity(corrupt_path, CompressionFormat.GZIP)
    assert res.status == VerificationStatus.FAIL
    assert res.crc_or_trailer_valid is False


def test_empty_file(tmp_path: Path):
    """Test 5: 0-byte file is identified correctly."""
    empty_path = tmp_path / "empty.gz"
    empty_path.write_bytes(b"")

    res = validate_compression_integrity(empty_path, CompressionFormat.GZIP)
    assert res.status == VerificationStatus.FAIL or res.decompressed_bytes == 0


def test_valid_empty_compressed_stream(tmp_path: Path):
    """Test 6: Valid compressed stream containing 0 decompressed bytes."""
    empty_gz = tmp_path / "valid_empty.gz"
    with gzip.open(empty_gz, "wb") as f:
        pass  # write 0 uncompressed bytes

    res = validate_compression_integrity(empty_gz, CompressionFormat.GZIP)
    assert res.status == VerificationStatus.PASS
    assert res.decompressed_bytes == 0
    assert res.crc_or_trailer_valid is True


def test_decompression_size_limit(tmp_path: Path):
    """Test 29: Stream exceeding max decompressed bytes limit triggers ResourceLimitExceededError."""
    data = b"0123456789" * 10_000  # 100 KB
    gz_path = tmp_path / "size_limit.gz"
    with gzip.open(gz_path, "wb") as f:
        f.write(data)

    # Set threshold low: 10 KB
    res = validate_compression_integrity(gz_path, CompressionFormat.GZIP, max_decompressed_size=10_000)
    assert res.status == VerificationStatus.FAIL
    assert "Security limit" in (res.error_message or "")


def test_expansion_ratio_protection(tmp_path: Path):
    """Test 30: Highly repetitive compression bomb stream triggers expansion ratio protection."""
    # 2 MB of zeroes compresses to ~2 KB (> 1000x expansion ratio)
    bomb_data = b"\x00" * 2_097_152
    gz_path = tmp_path / "bomb.gz"
    with gzip.open(gz_path, "wb") as f:
        f.write(bomb_data)

    # Ceiling is 20x
    res = validate_compression_integrity(gz_path, CompressionFormat.GZIP, max_expansion_ratio=20.0)
    assert res.status == VerificationStatus.FAIL
    assert "Security limit" in (res.error_message or "")

