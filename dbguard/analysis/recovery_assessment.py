"""Module 11: Algorithm E — Recovery Assessment Engine.

Synthesizes physical compression checks, parsing diagnostics, cryptographic hashes,
and manifest verification into a scoped, defensible recovery classification.
Explicitly documents what has been verified and what remains unverified.
"""

from typing import List, Optional

from dbguard.models import (
    Anomaly,
    AnomalySeverity,
    CompressionValidationResult,
    FileInspection,
    ManifestProvenance,
    ManifestVerificationResult,
    ParsingResult,
    RecoveryAssessment,
    RecoveryClassification,
    VerificationStatus,
)


def assess_recovery_feasibility(
    file_inspection: FileInspection,
    compression_validation: CompressionValidationResult,
    parsing_result: ParsingResult,
    manifest_verification: Optional[ManifestVerificationResult] = None,
    anomalies: Optional[List[Anomaly]] = None,
) -> RecoveryAssessment:
    """Evaluate export usability for disaster recovery or database restoration.

    Args:
        file_inspection: Intake inspection.
        compression_validation: Physical decompression integrity.
        parsing_result: Structural parsing metrics.
        manifest_verification: Manifest evaluation results.
        anomalies: Detected anomalies list.

    Returns:
        RecoveryAssessment with standardized classification, verified properties, and limitations.
    """
    verified_props: List[str] = []
    unverified_props: List[str] = []
    failures: List[str] = []
    recommended_actions: List[str] = []
    evidence_needed: List[str] = []

    # 1. Evaluate Format Validity
    if not file_inspection.is_valid_header or compression_validation.status == VerificationStatus.NOT_APPLICABLE:
        return RecoveryAssessment(
            classification=RecoveryClassification.UNSUPPORTED_FORMAT,
            summary="Export rejected due to unsupported or ambiguous file format.",
            verified_properties=[],
            unverified_or_inconclusive=["All data contents and integrity properties."],
            failures=["Unrecognized compression container or file header."],
            recoverable_record_estimate=0,
            recommended_actions=[
                "Confirm export file extension and ensure it matches supported formats (gzip, bz2, xz, zstd, csv, jsonl, sql).",
                "Ensure file is not corrupted during download or network transfer."
            ],
            evidence_needed_for_full_claim=["Valid file format header."]
        )

    # 2. Evaluate Inconclusive / Empty States
    if file_inspection.is_empty or (parsing_result.record_count == 0 and not parsing_result.header):
        return RecoveryAssessment(
            classification=RecoveryClassification.INCONCLUSIVE,
            summary="Export file is empty or contains zero records.",
            verified_properties=[],
            unverified_or_inconclusive=["Data completeness and usability."],
            failures=["File size is 0 bytes or zero records parsed."],
            recoverable_record_estimate=0,
            recommended_actions=["Check database export script logs to determine why no rows were emitted."],
            evidence_needed_for_full_claim=["Non-empty export payload."]
        )

    # 3. Check Physical Compression Stream
    if compression_validation.status == VerificationStatus.FAIL:
        failures.append(f"Physical compression container integrity failure: {compression_validation.error_message}")
        if compression_validation.is_truncated:
            failures.append("Compression stream was truncated before trailer/EOF.")
        return RecoveryAssessment(
            classification=RecoveryClassification.INTEGRITY_FAILURE,
            summary="Physical compression container is corrupted or truncated. Reliable recovery is not possible.",
            verified_properties=[],
            unverified_or_inconclusive=["Unreadable payload beyond corruption offset."],
            failures=failures,
            recoverable_record_estimate=parsing_result.record_count if parsing_result.record_count > 0 else 0,
            recommended_actions=[
                "Do NOT rely on this export file for disaster recovery.",
                "Re-generate export from source database immediately.",
                "If only a partial salvage is possible, extract records up to the corruption offset."
            ],
            evidence_needed_for_full_claim=["Intact, uncorrupted compression stream."]
        )

    verified_props.append(f"Compression container is physically intact ({compression_validation.format.value}).")
    verified_props.append(f"Decompressed byte stream verified ({compression_validation.decompressed_bytes:,} bytes).")

    # 4. Check Manifest Verification
    manifest_passed = False
    is_trusted_pipeline = False

    if manifest_verification:
        if manifest_verification.manifest_provenance == ManifestProvenance.TRUSTED_EXPORT_PIPELINE:
            is_trusted_pipeline = True

        if manifest_verification.overall_status == VerificationStatus.FAIL:
            for check in manifest_verification.checks:
                if check.status == VerificationStatus.FAIL:
                    failures.append(f"Manifest failure on '{check.field_name}': {check.message}")
            return RecoveryAssessment(
                classification=RecoveryClassification.INTEGRITY_FAILURE,
                summary="Export contradicts trusted manifest declarations (row count or cryptographic hash mismatch).",
                verified_properties=verified_props,
                unverified_or_inconclusive=[],
                failures=failures,
                recoverable_record_estimate=parsing_result.record_count,
                recommended_actions=[
                    "Investigate export pipeline for dropped rows or post-export data tampering.",
                    "Verify source database row count at time of export."
                ],
                evidence_needed_for_full_claim=["Concordance with trusted manifest."]
            )
        elif manifest_verification.overall_status == VerificationStatus.PASS:
            manifest_passed = True
            verified_props.append(f"Passed all manifest declarations (provenance: {manifest_verification.manifest_provenance.value}).")

    # 5. Check Structural Parsing Results
    has_parse_errors = (parsing_result.malformed_record_count > 0)
    if has_parse_errors:
        failures.append(f"Encountered {parsing_result.malformed_record_count:,} malformed record(s) during parsing.")
        estimated_recoverable = max(0, parsing_result.record_count - parsing_result.malformed_record_count)
        return RecoveryAssessment(
            classification=RecoveryClassification.RECOVERY_POSSIBLE_WITH_ERRORS,
            summary=(
                f"Export is readable but contains {parsing_result.malformed_record_count:,} malformed records. "
                f"Approximately {estimated_recoverable:,} records appear recoverable."
            ),
            verified_properties=verified_props,
            unverified_or_inconclusive=["Integrity of malformed lines."],
            failures=failures,
            recoverable_record_estimate=estimated_recoverable,
            recommended_actions=[
                "Isolate malformed line numbers captured in the parsing diagnostics.",
                "Verify whether delimiter escaping or quote nesting caused row corruption.",
                "Apply sanitization or row-recovery scripts to salvage unaffected rows."
            ],
            evidence_needed_for_full_claim=["Zero malformed records and consistent column structures."]
        )

    verified_props.append(f"All {parsing_result.record_count:,} records parsed cleanly with consistent column structure.")

    # 6. Differentiate Fully Verified vs Likely Usable
    if manifest_passed and is_trusted_pipeline:
        return RecoveryAssessment(
            classification=RecoveryClassification.VERIFIED_WITHIN_SCOPE,
            summary="Export is fully verified within scope: compression stream, row count, schema, and checksums match the trusted manifest.",
            verified_properties=verified_props,
            unverified_or_inconclusive=[
                "Unindexed internal field values not covered by chunk or record hashes."
            ],
            failures=[],
            recoverable_record_estimate=parsing_result.record_count,
            recommended_actions=[
                "Export is suitable for restoration or archival recovery workflows.",
                "Retain integrity manifest alongside the export archive."
            ],
            evidence_needed_for_full_claim=[]
        )

    # 7. Otherwise: LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED
    unverified_props.append(
        "Source database completeness: Without an independent pipeline manifest or direct database query, "
        "it cannot be proven that the export captured every table row."
    )
    if not manifest_verification:
        evidence_needed.append("Cryptographic manifest generated synchronously at export creation time.")
    elif manifest_verification.manifest_provenance == ManifestProvenance.OBSERVATIONAL_POST_HOC:
        unverified_props.append("Manifest was generated post-hoc and cannot prove original source completeness.")
        evidence_needed.append("Pipeline-generated manifest with source database row count reference.")

    # Check if size anomaly exists
    size_anomaly = any(a.rule_id == "RULE_SIZE_DROP_ROW_INCREASE" for a in (anomalies or []))
    if size_anomaly:
        unverified_props.append("Size anomaly present: export file size is smaller despite having more rows.")

    return RecoveryAssessment(
        classification=RecoveryClassification.LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED,
        summary=(
            f"Export decompresses and parses cleanly ({parsing_result.record_count:,} records). "
            "However, source completeness is NOT fully proven due to absence of an independent pipeline manifest."
        ),
        verified_properties=verified_props,
        unverified_or_inconclusive=unverified_props,
        failures=[],
        recoverable_record_estimate=parsing_result.record_count,
        recommended_actions=[
            "Compare record count against source database audit logs (e.g. SELECT COUNT(*) FROM table).",
            "Establish export-time manifest generation for future backup runs.",
            "Verify data entropy and schema to confirm that smaller file size reflects legitimate repetition."
        ],
        evidence_needed_for_full_claim=evidence_needed
    )

