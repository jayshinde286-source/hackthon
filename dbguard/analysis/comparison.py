"""Module 9: Export Comparison Engine.

Performs structured comparison between an earlier export baseline and a newer export.
Calculates percentage changes, ratio shifts, bytes-per-row variations, and schema diffs.
"""

from typing import List, Optional, Set
from dbguard.analysis.statistics import (
    safe_percentage_change,
    calculate_compression_ratio,
    calculate_bytes_per_row,
)
from dbguard.models import ExportComparison, ExportMetrics, MetricDiff


def compare_exports(
    old_metrics: ExportMetrics,
    new_metrics: ExportMetrics,
    old_header: Optional[List[str]] = None,
    new_header: Optional[List[str]] = None,
) -> ExportComparison:
    """Compare two exports and evaluate structural, physical, and metric shifts.

    Args:
        old_metrics: Baseline export metrics.
        new_metrics: Current export metrics.
        old_header: Baseline column names list.
        new_header: Current column names list.

    Returns:
        ExportComparison with detailed diffs, schema changes, and anomaly flags.
    """
    diffs: List[MetricDiff] = []
    anomaly_flags: List[str] = []

    # 1. Row Count Diff
    row_abs = new_metrics.row_count - old_metrics.row_count
    row_pct = safe_percentage_change(old_metrics.row_count, new_metrics.row_count)
    diffs.append(MetricDiff(
        metric_name="row_count",
        old_value=old_metrics.row_count,
        new_value=new_metrics.row_count,
        absolute_change=row_abs,
        percentage_change=row_pct
    ))

    # 2. Compressed Size Diff
    comp_abs = new_metrics.compressed_size_bytes - old_metrics.compressed_size_bytes
    comp_pct = safe_percentage_change(old_metrics.compressed_size_bytes, new_metrics.compressed_size_bytes)
    diffs.append(MetricDiff(
        metric_name="compressed_size_bytes",
        old_value=old_metrics.compressed_size_bytes,
        new_value=new_metrics.compressed_size_bytes,
        absolute_change=comp_abs,
        percentage_change=comp_pct
    ))

    # 3. Decompressed Size Diff
    decomp_abs = new_metrics.decompressed_size_bytes - old_metrics.decompressed_size_bytes
    decomp_pct = safe_percentage_change(old_metrics.decompressed_size_bytes, new_metrics.decompressed_size_bytes)
    diffs.append(MetricDiff(
        metric_name="decompressed_size_bytes",
        old_value=old_metrics.decompressed_size_bytes,
        new_value=new_metrics.decompressed_size_bytes,
        absolute_change=decomp_abs,
        percentage_change=decomp_pct
    ))

    # 4. Compression Ratio Diff
    ratio_abs = round(new_metrics.compression_ratio - old_metrics.compression_ratio, 4)
    ratio_pct = safe_percentage_change(old_metrics.compression_ratio, new_metrics.compression_ratio)
    diffs.append(MetricDiff(
        metric_name="compression_ratio",
        old_value=old_metrics.compression_ratio,
        new_value=new_metrics.compression_ratio,
        absolute_change=ratio_abs,
        percentage_change=ratio_pct
    ))

    # 5. Bytes Per Row Diff
    bpr_abs = round(new_metrics.bytes_per_row - old_metrics.bytes_per_row, 2)
    bpr_pct = safe_percentage_change(old_metrics.bytes_per_row, new_metrics.bytes_per_row)
    diffs.append(MetricDiff(
        metric_name="bytes_per_row",
        old_value=old_metrics.bytes_per_row,
        new_value=new_metrics.bytes_per_row,
        absolute_change=bpr_abs,
        percentage_change=bpr_pct
    ))

    # Schema comparison
    schema_match = (old_metrics.schema_fingerprint == new_metrics.schema_fingerprint)
    old_cols: Set[str] = set(old_header or [])
    new_cols: Set[str] = set(new_header or [])
    added = sorted(list(new_cols - old_cols))
    removed = sorted(list(old_cols - new_cols))

    # Evaluate Specific Anomaly Conditions
    if row_pct is not None and comp_pct is not None:
        if row_pct > 0 and comp_pct < 0:
            anomaly_flags.append(
                f"Row count increased (+{row_pct:.1f}%), yet compressed file size decreased ({comp_pct:.1f}%). "
                f"Requires investigation into data entropy, repetitive patterns, or missing columns."
            )
        elif row_pct < -5.0 and comp_pct < -5.0:
            anomaly_flags.append(
                f"Both row count ({row_pct:.1f}%) and file size ({comp_pct:.1f}%) dropped substantially. "
                f"Possible incomplete export or data purging."
            )

    if not schema_match:
        anomaly_flags.append(
            f"Schema mismatch detected: Fingerprint changed. Added columns: {added or 'None'}, Removed: {removed or 'None'}."
        )

    if new_metrics.malformed_count > old_metrics.malformed_count:
        anomaly_flags.append(
            f"Malformed record count increased from {old_metrics.malformed_count} to {new_metrics.malformed_count}."
        )

    summary_verdict = (
        f"Compared {old_metrics.row_count:,} rows ({old_metrics.compressed_size_bytes:,} B) -> "
        f"{new_metrics.row_count:,} rows ({new_metrics.compressed_size_bytes:,} B). "
        f"{'Anomalies flagged for review.' if anomaly_flags else 'Metrics consistent with expected operational growth.'}"
    )

    return ExportComparison(
        old_metrics=old_metrics,
        new_metrics=new_metrics,
        diffs=diffs,
        schema_match=schema_match,
        added_columns=added,
        removed_columns=removed,
        summary_verdict=summary_verdict,
        anomaly_flags=anomaly_flags
    )

