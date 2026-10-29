"""Tests for Module 8: Trusted Integrity Manifest Generation and Verification."""

import json
from pathlib import Path
import pytest

from dbguard.manifest.generator import generate_manifest
from dbguard.manifest.schema import validate_manifest_dict
from dbguard.manifest.verifier import verify_manifest
from dbguard.models import (
    CompressionFormat,
    CompressionValidationResult,
    ExportFormat,
    FileInspection,
    HashResult,
    ManifestProvenance,
    ParsingResult,
    VerificationStatus,
)


@pytest.fixture
def dummy_results():
    fi = FileInspection(
        path="/tmp/test.csv.gz",
        filename="test.csv.gz",
        file_size_bytes=1000,
        detected_compression=CompressionFormat.GZIP,
        sha256_compressed="a" * 64,
        is_empty=False,
        is_valid_header=True,
        header_hex="1f8b",
    )
    comp = CompressionValidationResult(
        status=VerificationStatus.PASS,
        format=CompressionFormat.GZIP,
        compressed_bytes_read=1000,
        decompressed_bytes=4000,
        expansion_ratio=4.0,
        sha256_decompressed="b" * 64,
        is_truncated=False,
    )
    parse = ParsingResult(
        status=VerificationStatus.PASS,
        format=ExportFormat.CSV,
        header=["id", "name"],
        column_count=2,
        record_count=100,
        malformed_record_count=0,
        empty_value_count=0,
        schema_fingerprint="c" * 64,
    )
    hashes = HashResult(
        compressed_sha256="a" * 64,
        decompressed_sha256="b" * 64,
        chunk_hashes=[],
        merkle_root="d" * 64,
    )
    return fi, comp, parse, hashes


def test_matching_trusted_manifest(dummy_results):
    """Test 16: Matching trusted manifest yields PASS."""
    fi, comp, parse, hashes = dummy_results
    manifest = generate_manifest(
        export_id="EXP-1",
        source_identifier="tbl_test",
        export_format="csv",
        compression_format="gzip",
        schema_fingerprint=parse.schema_fingerprint,
        expected_row_count=parse.record_count,
        uncompressed_size_bytes=comp.decompressed_bytes,
        uncompressed_sha256=hashes.decompressed_sha256,
        compressed_size_bytes=fi.file_size_bytes,
        compressed_sha256=fi.sha256_compressed,
        trusted_reference_status=ManifestProvenance.TRUSTED_EXPORT_PIPELINE
    )

    res = verify_manifest(manifest, fi, comp, parse, hashes)
    assert res.overall_status == VerificationStatus.PASS
    assert all(c.status in (VerificationStatus.PASS, VerificationStatus.NOT_APPLICABLE) for c in res.checks)


def test_incorrect_manifest_hash(dummy_results):
    """Test 17: Incorrect uncompressed hash in manifest fails verification."""
    fi, comp, parse, hashes = dummy_results
    manifest = generate_manifest(
        export_id="EXP-1",
        source_identifier="tbl_test",
        export_format="csv",
        compression_format="gzip",
        schema_fingerprint=parse.schema_fingerprint,
        expected_row_count=parse.record_count,
        uncompressed_size_bytes=comp.decompressed_bytes,
        uncompressed_sha256="f" * 64,  # Intentionally wrong hash!
        trusted_reference_status=ManifestProvenance.TRUSTED_EXPORT_PIPELINE
    )

    res = verify_manifest(manifest, fi, comp, parse, hashes)
    assert res.overall_status == VerificationStatus.FAIL
    hash_check = next(c for c in res.checks if c.field_name == "uncompressed_sha256")
    assert hash_check.status == VerificationStatus.FAIL


def test_incorrect_expected_row_count(dummy_results):
    """Test 18: Incorrect expected row count fails verification."""
    fi, comp, parse, hashes = dummy_results
    manifest = generate_manifest(
        export_id="EXP-1",
        source_identifier="tbl_test",
        export_format="csv",
        compression_format="gzip",
        schema_fingerprint=parse.schema_fingerprint,
        expected_row_count=999_999,  # Intentionally wrong row count!
        uncompressed_size_bytes=comp.decompressed_bytes,
        uncompressed_sha256=hashes.decompressed_sha256,
        trusted_reference_status=ManifestProvenance.TRUSTED_EXPORT_PIPELINE
    )

    res = verify_manifest(manifest, fi, comp, parse, hashes)
    assert res.overall_status == VerificationStatus.FAIL
    row_check = next(c for c in res.checks if c.field_name == "row_count")
    assert row_check.status == VerificationStatus.FAIL


def test_missing_manifest_fields():
    """Test 19: Manifest missing required schema fields is rejected."""
    bad_manifest = {
        "manifest_version": "1.0",
        "export_id": "EXP-BAD",
        # missing expected_row_count, uncompressed_sha256, etc.
    }
    with pytest.raises(Exception):
        validate_manifest_dict(bad_manifest)


def test_unsupported_manifest_version():
    """Test 20: Unsupported manifest version raises error."""
    future_manifest = {
        "manifest_version": "99.0",
        "export_id": "EXP-FUTURE",
    }
    with pytest.raises(Exception):
        validate_manifest_dict(future_manifest)


def test_untrusted_manifest_provenance(dummy_results):
    """Test 21: Manifest generated post-hoc is marked with provenance warning."""
    fi, comp, parse, hashes = dummy_results
    manifest = generate_manifest(
        export_id="EXP-POST-HOC",
        source_identifier="tbl_test",
        export_format="csv",
        compression_format="gzip",
        schema_fingerprint=parse.schema_fingerprint,
        expected_row_count=parse.record_count,
        uncompressed_size_bytes=comp.decompressed_bytes,
        uncompressed_sha256=hashes.decompressed_sha256,
        trusted_reference_status=ManifestProvenance.OBSERVATIONAL_POST_HOC
    )

    res = verify_manifest(manifest, fi, comp, parse, hashes)
    assert res.manifest_provenance == ManifestProvenance.OBSERVATIONAL_POST_HOC
    assert res.provenance_warning is not None
    assert "OBSERVATIONAL" in res.provenance_warning

