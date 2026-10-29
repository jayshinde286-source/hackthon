"""Tests for Module 9 & 10: Export Comparison and Anomaly Detection."""

import pytest
from dbguard.analysis.anomalies import detect_anomalies
from dbguard.analysis.comparison import compare_exports
from dbguard.models import (
    AnomalySeverity,
    CompressionFormat,
    ExportMetrics,
    FileInspection,
    HashResult,
    ParsingResult,
    VerificationStatus,
    ExportFormat,
)


def test_identical_exports_comparison():
    """Test 22: Comparing identical export metrics produces zero percent changes and matches schema."""
    m = ExportMetrics(
        compressed_size_bytes=100_000,
        decompressed_size_bytes=400_000,
        row_count=10_000,
        compression_ratio=4.0,
        bytes_per_row=40.0,
        schema_fingerprint="abc123",
        column_count=5,
        malformed_count=0
    )
    cmp = compare_exports(m, m, old_header=["a", "b"], new_header=["a", "b"])
    assert cmp.schema_match is True
    assert len(cmp.anomaly_flags) == 0
    row_diff = next(d for d in cmp.diffs if d.metric_name == "row_count")
    assert row_diff.absolute_change == 0
    assert row_diff.percentage_change == 0.0


def test_different_exports_same_row_count():
    """Test 23: Different exports with the exact same row count."""
    m_old = ExportMetrics(100_000, 400_000, 10_000, 4.0, 40.0, "abc123", 5, 0)
    m_new = ExportMetrics(110_000, 410_000, 10_000, 3.72, 41.0, "abc123", 5, 0)
    cmp = compare_exports(m_old, m_new)
    assert cmp.schema_match is True
    row_diff = next(d for d in cmp.diffs if d.metric_name == "row_count")
    assert row_diff.percentage_change == 0.0


def test_larger_export_smaller_compressed_size():
    """Test 24 (The Official Problem Statement Scenario):
    Row count increases by +30%, but compressed file size decreases by -20%.
    Detected as RULE_SIZE_DROP_ROW_INCREASE warning without false corruption claim.
    """
    m_old = ExportMetrics(
        compressed_size_bytes=100_000_000,  # 100 MB
        decompressed_size_bytes=400_000_000, # 400 MB
        row_count=100_000,
        compression_ratio=4.0,
        bytes_per_row=4000.0,
        schema_fingerprint="fp1",
        column_count=10,
        malformed_count=0
    )
    m_new = ExportMetrics(
        compressed_size_bytes=80_000_000,    # 80 MB (-20%)
        decompressed_size_bytes=450_000_000, # 450 MB (+12.5%)
        row_count=130_000,                   # 130,000 (+30%)
        compression_ratio=5.625,
        bytes_per_row=3461.5,
        schema_fingerprint="fp1",
        column_count=10,
        malformed_count=0
    )

    cmp = compare_exports(m_old, m_new)
    assert any("Row count increased (+30.0%), yet compressed file size decreased (-20.0%)" in flag for flag in cmp.anomaly_flags)

    # Verify anomaly detector flags it with explanation
    fi = FileInspection("/tmp/new.gz", "new.gz", 80_000_000, CompressionFormat.GZIP, "sha", False, True, "1f8b")
    pr = ParsingResult(VerificationStatus.PASS, ExportFormat.CSV, ["id"], 1, 130_000, 0, 0, "fp1", [], [], 0, 450_000_000)
    hr = HashResult("sha_c", "sha_d")

    anomalies = detect_anomalies(fi, pr, hr, comparison=cmp)
    size_anomaly = next((a for a in anomalies if a.rule_id == "RULE_SIZE_DROP_ROW_INCREASE"), None)
    assert size_anomaly is not None
    assert size_anomaly.severity == AnomalySeverity.WARNING
    assert "repetition" in size_anomaly.explanation.lower()


def test_schema_mismatch_detection():
    """Test 26: Schema fingerprint change is flagged with added and removed columns."""
    m_old = ExportMetrics(1000, 4000, 100, 4.0, 40.0, "fingerprint_v1", 2, 0)
    m_new = ExportMetrics(1000, 4000, 100, 4.0, 40.0, "fingerprint_v2", 3, 0)

    cmp = compare_exports(m_old, m_new, old_header=["id", "name"], new_header=["id", "name", "email"])
    assert cmp.schema_match is False
    assert cmp.added_columns == ["email"]
    assert len(cmp.removed_columns) == 0


def test_statistical_anomaly_insufficient_history():
    """Test 27: Statistical checks report limited confidence when fewer than 5 historical exports exist."""
    fi = FileInspection("/tmp/x.gz", "x.gz", 1000, CompressionFormat.GZIP, "s", False, True, "1f8b")
    pr = ParsingResult(VerificationStatus.PASS, ExportFormat.CSV, ["id"], 1, 100, 0, 0, "fp", [], [], 0, 4000)
    hr = HashResult("sc", "sd")

    # Only 2 historical samples
    short_history = [
        ExportMetrics(1000, 4000, 100, 4.0, 40.0, "fp", 1, 0),
        ExportMetrics(1050, 4200, 105, 4.0, 40.0, "fp", 1, 0),
    ]

    anomalies = detect_anomalies(fi, pr, hr, historical_metrics=short_history)
    info_flag = next((a for a in anomalies if a.rule_id == "RULE_STATISTICAL_CONFIDENCE_LIMITED"), None)
    assert info_flag is not None
    assert info_flag.severity == AnomalySeverity.INFO

