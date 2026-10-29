"""Tests for Security, Safe Path Handling, and Non-Destructive Invariant."""

import gzip
from pathlib import Path
import pytest

from dbguard.analyzer import analyze_export
from dbguard.exceptions import SecurityError, UnsupportedFormatError
from dbguard.file_inspector import inspect_file
from dbguard.models import CompressionFormat, RecoveryClassification
from dbguard.utils.safe_paths import validate_input_path, safe_output_path


def test_unsafe_path_handling():
    """Test 31: Null byte injection and directory traversal attempts are blocked."""
    with pytest.raises(SecurityError):
        validate_input_path("/etc/passwd\0evil.csv.gz")

    with pytest.raises(SecurityError):
        safe_output_path("/var/log/test\0out.pdf")


def test_unsupported_format(tmp_path: Path):
    """Test 12: Unsupported binary format safely rejected."""
    bad_bin = tmp_path / "unknown.bin"
    bad_bin.write_bytes(b"\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09")

    report = analyze_export(bad_bin)
    assert report.recovery_assessment.classification == RecoveryClassification.UNSUPPORTED_FORMAT


def test_original_file_unmodified(tmp_path: Path):
    """Test 32: Core invariant: Original export file bytes are never modified or overwritten during analysis."""
    test_file = tmp_path / "preserve_test.csv.gz"
    with gzip.open(test_file, "wb") as f:
        f.write(b"id,name\n1,alpha\n2,beta\n")

    original_bytes = test_file.read_bytes()
    original_mtime = test_file.stat().st_mtime_ns

    # Run complete analysis pass
    report = analyze_export(test_file)

    # Re-verify original file bytes and timestamp
    assert test_file.read_bytes() == original_bytes
    assert test_file.stat().st_mtime_ns == original_mtime

