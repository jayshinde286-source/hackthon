"""Module 12: CSV Summary Report Generator."""

import csv
import io
from pathlib import Path
from typing import Optional, Union
from dbguard.models import AnalysisReport
from dbguard.utils.safe_paths import safe_output_path


def generate_csv_report(report: AnalysisReport, output_path: Optional[Union[str, Path]] = None) -> str:
    """Generate a tabular CSV summary of the analysis report."""
    out = io.StringIO()
    writer = csv.writer(out)

    writer.writerow(["DBGuard Analysis Summary Report"])
    writer.writerow(["Report ID", report.report_id])
    writer.writerow(["Generated At (UTC)", report.generated_at_utc])
    writer.writerow(["Execution Duration (sec)", report.execution_duration_sec])
    writer.writerow([])

    writer.writerow(["SECTION", "METRIC / FIELD", "VALUE", "STATUS / NOTES"])
    writer.writerow(["File Intake", "Filename", report.file_inspection.filename, ""])
    writer.writerow(["File Intake", "Compressed File Size (bytes)", report.file_inspection.file_size_bytes, ""])
    writer.writerow(["File Intake", "Detected Compression", report.file_inspection.detected_compression.value, ""])
    writer.writerow(["File Intake", "Compressed SHA-256", report.file_inspection.sha256_compressed, ""])

    writer.writerow(["Compression Stream", "Status", report.compression_validation.status.value, ""])
    writer.writerow(["Compression Stream", "Decompressed Size (bytes)", report.compression_validation.decompressed_bytes, ""])
    writer.writerow(["Compression Stream", "Expansion Ratio", f"{report.compression_validation.expansion_ratio:.2f}x", ""])
    writer.writerow(["Compression Stream", "Decompressed SHA-256", report.compression_validation.sha256_decompressed, ""])
    writer.writerow(["Compression Stream", "CRC / Trailer Valid", str(report.compression_validation.crc_or_trailer_valid), ""])
    writer.writerow(["Compression Stream", "Truncated", str(report.compression_validation.is_truncated), ""])

    writer.writerow(["Data Parsing", "Status", report.parsing_result.status.value, ""])
    writer.writerow(["Data Parsing", "Data Format", report.parsing_result.format.value, ""])
    writer.writerow(["Data Parsing", "Parsed Records", report.parsing_result.record_count, ""])
    writer.writerow(["Data Parsing", "Columns", report.parsing_result.column_count, ""])
    writer.writerow(["Data Parsing", "Malformed Records", report.parsing_result.malformed_record_count, ""])
    writer.writerow(["Data Parsing", "Empty/Null Values", report.parsing_result.empty_value_count, ""])
    writer.writerow(["Data Parsing", "Schema Fingerprint", report.parsing_result.schema_fingerprint, ""])

    writer.writerow(["Hashing", "Merkle Root", report.hash_result.merkle_root or "N/A", ""])
    writer.writerow(["Hashing", "Chunk Count (1MB)", len(report.hash_result.chunk_hashes), ""])

    if report.manifest_verification:
        writer.writerow(["Manifest Verification", "Overall Status", report.manifest_verification.overall_status.value, ""])
        writer.writerow(["Manifest Verification", "Provenance", report.manifest_verification.manifest_provenance.value, ""])
        for chk in report.manifest_verification.checks:
            writer.writerow(["Manifest Check", chk.field_name, f"Expected: {chk.expected} | Observed: {chk.observed}", chk.status.value])

    writer.writerow(["Recovery Assessment", "Classification", report.recovery_assessment.classification.value, ""])
    writer.writerow(["Recovery Assessment", "Summary", report.recovery_assessment.summary, ""])
    writer.writerow(["Recovery Assessment", "Recoverable Records Estimate", report.recovery_assessment.recoverable_record_estimate, ""])

    if report.anomalies:
        writer.writerow([])
        writer.writerow(["ANOMALY RULE ID", "SEVERITY", "METRIC", "OBSERVED", "EXPLANATION"])
        for a in report.anomalies:
            writer.writerow([a.rule_id, a.severity.value, a.metric_name, str(a.observed_value), a.explanation])

    csv_content = out.getvalue()

    if output_path:
        p = safe_output_path(output_path, allow_overwrite=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(csv_content)

    return csv_content

