"""Module 10: Algorithm C — Explainable Rule-Based Anomaly Detection Engine.

Applies deterministic rules and robust statistical methods (Median Absolute Deviation)
to detect physical, structural, and logical anomalies across database exports.
Separates verifiable integrity failures from statistical anomalies.
"""

from typing import List, Optional, Dict, Any
from dbguard.analysis.statistics import (
    calculate_mad,
    calculate_median,
    safe_percentage_change,
)
from dbguard.models import (
    Anomaly,
    AnomalySeverity,
    ExportComparison,
    ExportMetrics,
    FileInspection,
    HashResult,
    ManifestVerificationResult,
    ParsingResult,
    VerificationStatus,
)

DEFAULT_THRESHOLDS = {
    "size_drop_row_increase_threshold_pct": 5.0,
    "bytes_per_row_change_threshold_pct": 25.0,
    "compression_ratio_change_threshold_pct": 30.0,
    "row_count_drop_threshold_pct": -10.0,
    "min_history_for_statistics": 5,
    "anomaly_mad_cutoff": 3.0,
}


def detect_anomalies(
    file_inspection: FileInspection,
    parsing_result: ParsingResult,
    hash_result: HashResult,
    manifest_verification: Optional[ManifestVerificationResult] = None,
    comparison: Optional[ExportComparison] = None,
    historical_metrics: Optional[List[ExportMetrics]] = None,
    thresholds: Optional[Dict[str, float]] = None,
) -> List[Anomaly]:
    """Execute Algorithm C: Explainable Rule-Based Anomaly Detection.

    Args:
        file_inspection: Intake inspection findings.
        parsing_result: Streaming parser metrics.
        hash_result: Cryptographic hashes.
        manifest_verification: Manifest evaluation results if available.
        comparison: Comparison with baseline export if available.
        historical_metrics: Optional list of past export metrics for statistical baseline.
        thresholds: Configurable detection thresholds.

    Returns:
        List of typed Anomaly objects with explanations and recommendations.
    """
    cfg = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        cfg.update(thresholds)

    anomalies: List[Anomaly] = []

    # Rule 12: Empty or unusually small export
    if file_inspection.file_size_bytes == 0:
        anomalies.append(Anomaly(
            rule_id="RULE_EMPTY_OR_UNUSUALLY_SMALL",
            severity=AnomalySeverity.CRITICAL,
            metric_name="file_size_bytes",
            observed_value=0,
            expected_or_baseline="> 0 bytes",
            threshold=1,
            explanation="The compressed export file is completely empty (0 bytes).",
            recommendation="Verify that the database export job executed successfully and that disk quota was not exhausted.",
            evidence_ref=f"File inspection of {file_inspection.filename}",
            confidence_limitations="Conclusive physical property."
        ))

    if parsing_result.record_count == 0 and not file_inspection.is_empty:
        anomalies.append(Anomaly(
            rule_id="RULE_EMPTY_OR_UNUSUALLY_SMALL",
            severity=AnomalySeverity.CRITICAL,
            metric_name="record_count",
            observed_value=0,
            expected_or_baseline="> 0 records",
            threshold=1,
            explanation="The export decompressed successfully but parsed zero data records.",
            recommendation="Check whether source table was empty or if the export query returned no rows.",
            evidence_ref=f"Parser record count for {file_inspection.filename}",
            confidence_limitations="Conclusive logical property."
        ))

    # Rule 13: Missing expected data sections / schema
    if parsing_result.column_count == 0:
        anomalies.append(Anomaly(
            rule_id="RULE_MISSING_DATA_SECTIONS",
            severity=AnomalySeverity.HIGH,
            metric_name="column_count",
            observed_value=0,
            expected_or_baseline=">= 1 column",
            threshold=1,
            explanation="No table columns or schema headers were recognized.",
            recommendation="Inspect file delimiter, quotation, or encoding settings.",
            evidence_ref="Streaming parser header detection",
            confidence_limitations="High confidence structural failure."
        ))

    # Rule 11: Unexpected parse errors
    if parsing_result.malformed_record_count > 0:
        sev = AnomalySeverity.CRITICAL if parsing_result.malformed_record_count > (parsing_result.record_count * 0.05) else AnomalySeverity.HIGH
        anomalies.append(Anomaly(
            rule_id="RULE_PARSE_ERRORS",
            severity=sev,
            metric_name="malformed_record_count",
            observed_value=parsing_result.malformed_record_count,
            expected_or_baseline=0,
            threshold=0,
            explanation=f"Detected {parsing_result.malformed_record_count:,} malformed records during parsing.",
            recommendation="Review parse error details for row numbers with column count mismatches or unescaped quotes.",
            evidence_ref=f"Parse error log ({len(parsing_result.errors)} samples captured)",
            confidence_limitations="Verifiable parsing defect."
        ))

    # Manifest-dependent Rules (Rules 4, 5, 6, 7, 8, 14)
    if manifest_verification:
        for check in manifest_verification.checks:
            if check.status == VerificationStatus.FAIL:
                if check.field_name == "row_count":
                    anomalies.append(Anomaly(
                        rule_id="RULE_MANIFEST_ROW_MISMATCH",
                        severity=AnomalySeverity.CRITICAL,
                        metric_name="row_count",
                        observed_value=check.observed,
                        expected_or_baseline=check.expected,
                        threshold="Exact Match",
                        explanation=f"Observed row count ({check.observed:,}) fails to match trusted manifest declaration ({check.expected:,}).",
                        recommendation="Do not use this export as a complete backup; investigate export job logs for premature termination.",
                        evidence_ref="Manifest vs Parser record count",
                        confidence_limitations="Conclusive failure when manifest is from a trusted export pipeline."
                    ))
                elif check.field_name == "uncompressed_sha256":
                    anomalies.append(Anomaly(
                        rule_id="RULE_DECOMPRESSED_HASH_MISMATCH",
                        severity=AnomalySeverity.CRITICAL,
                        metric_name="uncompressed_sha256",
                        observed_value=check.observed,
                        expected_or_baseline=check.expected,
                        threshold="Exact Match",
                        explanation="Decompressed byte stream SHA-256 does not match the trusted manifest hash.",
                        recommendation="The content of the decompressed stream has been altered or damaged.",
                        evidence_ref="Stream hasher digest comparison",
                        confidence_limitations="Cryptographically certain content mismatch."
                    ))
                elif check.field_name == "schema_fingerprint":
                    anomalies.append(Anomaly(
                        rule_id="RULE_SCHEMA_MISMATCH",
                        severity=AnomalySeverity.HIGH,
                        metric_name="schema_fingerprint",
                        observed_value=check.observed,
                        expected_or_baseline=check.expected,
                        threshold="Exact Match",
                        explanation="Schema structure differs from the trusted manifest declaration.",
                        recommendation="Verify whether database migrations altered columns before export.",
                        evidence_ref="Canonical schema fingerprint comparison",
                        confidence_limitations="High confidence structural change."
                    ))
                elif check.field_name == "chunk_hashes":
                    anomalies.append(Anomaly(
                        rule_id="RULE_CHUNK_HASH_MISMATCH",
                        severity=AnomalySeverity.HIGH,
                        metric_name="chunk_hashes",
                        observed_value=check.observed,
                        expected_or_baseline=check.expected,
                        threshold="Exact Match",
                        explanation="One or more 1MB byte chunks failed hash validation against manifest.",
                        recommendation="Isolate mismatched chunk byte offsets to locate damaged data segments.",
                        evidence_ref="Chunk hasher verification log",
                        confidence_limitations="Localized cryptographic mismatch."
                    ))

        if manifest_verification.provenance_warning:
            anomalies.append(Anomaly(
                rule_id="RULE_MANIFEST_METADATA_INCONSISTENCY",
                severity=AnomalySeverity.MEDIUM,
                metric_name="manifest_provenance",
                observed_value=manifest_verification.manifest_provenance.value,
                expected_or_baseline="TRUSTED_EXPORT_PIPELINE",
                threshold="Trusted Provenance",
                explanation=manifest_verification.provenance_warning,
                recommendation="Ensure manifests are created synchronously during export by the pipeline, not generated post-hoc.",
                evidence_ref="Manifest trusted_reference_status metadata",
                confidence_limitations="Completeness cannot be established from observational metadata alone."
            ))

    # Comparison-dependent Rules (Rules 1, 2, 3, 9, 10)
    if comparison:
        old_m = comparison.old_metrics
        new_m = comparison.new_metrics

        row_pct = safe_percentage_change(old_m.row_count, new_m.row_count)
        comp_pct = safe_percentage_change(old_m.compressed_size_bytes, new_m.compressed_size_bytes)
        decomp_pct = safe_percentage_change(old_m.decompressed_size_bytes, new_m.decompressed_size_bytes)
        ratio_pct = safe_percentage_change(old_m.compression_ratio, new_m.compression_ratio)
        bpr_pct = safe_percentage_change(old_m.bytes_per_row, new_m.bytes_per_row)

        # Rule 1: Central Problem Statement Anomaly: Size decrease despite row increase!
        if row_pct is not None and comp_pct is not None:
            if row_pct >= cfg["size_drop_row_increase_threshold_pct"] and comp_pct <= -cfg["size_drop_row_increase_threshold_pct"]:
                anomalies.append(Anomaly(
                    rule_id="RULE_SIZE_DROP_ROW_INCREASE",
                    severity=AnomalySeverity.WARNING,
                    metric_name="compressed_size_vs_row_count",
                    observed_value=f"Rows: +{row_pct:.1f}%, Size: {comp_pct:.1f}%",
                    expected_or_baseline="Compressed size generally scales with row count",
                    threshold=f"+{cfg['size_drop_row_increase_threshold_pct']}% rows / -{cfg['size_drop_row_increase_threshold_pct']}% size",
                    explanation=(
                        f"Export file size decreased by {abs(comp_pct):.1f}% despite row count increasing by {row_pct:.1f}%. "
                        "This anomaly does NOT automatically indicate corruption: higher compression dictionary efficiency, "
                        "increased repetition of string values, or high frequency of NULLs can legitimately produce smaller compressed outputs."
                    ),
                    recommendation="Investigate entropy, bytes-per-row, and data distribution before concluding corruption.",
                    evidence_ref="ExportComparison metric diffs",
                    confidence_limitations="Statistical and physical anomaly; requires independent manifest or entropy analysis to verify completeness."
                ))

        # Rule 2: Uncompressed size decrease despite row increase
        if row_pct is not None and decomp_pct is not None:
            if row_pct >= 5.0 and decomp_pct <= -5.0:
                anomalies.append(Anomaly(
                    rule_id="RULE_UNCOMP_SIZE_DECREASE",
                    severity=AnomalySeverity.HIGH,
                    metric_name="decompressed_size_vs_row_count",
                    observed_value=f"Rows: +{row_pct:.1f}%, Decompressed: {decomp_pct:.1f}%",
                    expected_or_baseline="Uncompressed size scales with row count",
                    threshold="Rows +5% / Decompressed -5%",
                    explanation=(
                        f"Raw decompressed data size decreased by {abs(decomp_pct):.1f}% while row count increased by {row_pct:.1f}%. "
                        "This indicates that average record length has shrunk significantly."
                    ),
                    recommendation="Verify whether long text columns were truncated or populated with empty/null strings.",
                    evidence_ref="Decompressed byte count diff",
                    confidence_limitations="Structural change; legitimate only if recent data has much shorter field values."
                ))

        # Rule 3: Unexpected row count drop
        if row_pct is not None and row_pct <= cfg["row_count_drop_threshold_pct"]:
            anomalies.append(Anomaly(
                rule_id="RULE_UNEXPECTED_ROW_CHANGE",
                severity=AnomalySeverity.HIGH,
                metric_name="row_count",
                observed_value=f"{row_pct:.1f}% change",
                expected_or_baseline="Monotonic growth or mild variation",
                threshold=f"{cfg['row_count_drop_threshold_pct']}%",
                explanation=f"Row count dropped by {abs(row_pct):.1f}% compared to previous export.",
                recommendation="Confirm whether intentional table truncation or archiving occurred.",
                evidence_ref="Previous export comparison",
                confidence_limitations="Context dependent."
            ))

        # Rule 9: Compression ratio shift
        if ratio_pct is not None and abs(ratio_pct) >= cfg["compression_ratio_change_threshold_pct"]:
            anomalies.append(Anomaly(
                rule_id="RULE_COMPRESSION_RATIO_SHIFT",
                severity=AnomalySeverity.MEDIUM,
                metric_name="compression_ratio",
                observed_value=f"{new_m.compression_ratio:.2f} ({ratio_pct:+.1f}%)",
                expected_or_baseline=f"{old_m.compression_ratio:.2f}",
                threshold=f"+/- {cfg['compression_ratio_change_threshold_pct']}%",
                explanation=f"Compression ratio changed by {ratio_pct:+.1f}% (from {old_m.compression_ratio:.2f}x to {new_m.compression_ratio:.2f}x).",
                recommendation="Examine if compression level settings, utility flags, or data compressibility changed.",
                evidence_ref="Compression ratio comparison",
                confidence_limitations="Compression ratio depends on data repetition and algorithm parameters."
            ))

        # Rule 10: Bytes per row shift
        if bpr_pct is not None and abs(bpr_pct) >= cfg["bytes_per_row_change_threshold_pct"]:
            anomalies.append(Anomaly(
                rule_id="RULE_BYTES_PER_ROW_SHIFT",
                severity=AnomalySeverity.MEDIUM,
                metric_name="bytes_per_row",
                observed_value=f"{new_m.bytes_per_row:.1f} B/row ({bpr_pct:+.1f}%)",
                expected_or_baseline=f"{old_m.bytes_per_row:.1f} B/row",
                threshold=f"+/- {cfg['bytes_per_row_change_threshold_pct']}%",
                explanation=f"Average bytes per data row shifted by {bpr_pct:+.1f}% (from {old_m.bytes_per_row:.1f} to {new_m.bytes_per_row:.1f} B/row).",
                recommendation="Inspect whether nullable fields or shorter categorical codes were recently introduced.",
                evidence_ref="Bytes per row calculation",
                confidence_limitations="Metric reflects average record length variance."
            ))

    # Historical Statistical Analysis (MAD / IQR)
    if historical_metrics is not None:
        min_hist = int(cfg["min_history_for_statistics"])
        if len(historical_metrics) < min_hist:
            anomalies.append(Anomaly(
                rule_id="RULE_STATISTICAL_CONFIDENCE_LIMITED",
                severity=AnomalySeverity.INFO,
                metric_name="historical_sample_size",
                observed_value=len(historical_metrics),
                expected_or_baseline=f">= {min_hist} historical exports",
                threshold=min_hist,
                explanation=f"Historical dataset contains {len(historical_metrics)} exports. Statistical confidence is limited.",
                recommendation="Accumulate at least 5 baseline exports before applying statistical outlier rejection.",
                evidence_ref="Historical export collection",
                confidence_limitations="Sample size too small for statistical certainty."
            ))
        else:
            # Evaluate current bytes_per_row against historical MAD
            hist_bpr = [m.bytes_per_row for m in historical_metrics]
            med_bpr = calculate_median(hist_bpr)
            mad_bpr = calculate_mad(hist_bpr, med_bpr)
            current_bpr = (parsing_result.bytes_consumed / max(1, parsing_result.record_count))

            cutoff = cfg["anomaly_mad_cutoff"] * max(mad_bpr, 1.0)
            if abs(current_bpr - med_bpr) > cutoff:
                anomalies.append(Anomaly(
                    rule_id="RULE_HISTORICAL_BPR_OUTLIER",
                    severity=AnomalySeverity.MEDIUM,
                    metric_name="bytes_per_row_vs_history",
                    observed_value=f"{current_bpr:.1f} B/row",
                    expected_or_baseline=f"Median: {med_bpr:.1f} B/row (MAD: {mad_bpr:.1f})",
                    threshold=f"> {cfg['anomaly_mad_cutoff']}x MAD deviation",
                    explanation=f"Current bytes per row ({current_bpr:.1f}) is a statistical outlier relative to historical baseline.",
                    recommendation="Review recent database schema changes, batch inserts, or data volume anomalies.",
                    evidence_ref="Historical Median Absolute Deviation (MAD) analysis",
                    confidence_limitations="Statistical inference based on historical distribution."
                ))

    return anomalies

