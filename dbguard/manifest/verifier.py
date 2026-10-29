"""Module 8: Algorithm B — Trusted Manifest Verification.

Executes granular comparison between observed export metrics and trusted manifest declarations.
Reports individual field checks, establishes provenance limitations, and avoids false completeness claims.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dbguard.manifest.schema import validate_manifest_dict
from dbguard.manifest.trust import evaluate_provenance, verify_manifest_hmac_signature
from dbguard.models import (
    ChunkHashEntry,
    CompressionValidationResult,
    FileInspection,
    HashResult,
    ManifestCheckDetail,
    ManifestProvenance,
    ManifestVerificationResult,
    ParsingResult,
    VerificationStatus,
)


def verify_manifest(
    manifest_data_or_path: Union[str, Path, Dict[str, Any]],
    file_inspection: FileInspection,
    compression_validation: CompressionValidationResult,
    parsing_result: ParsingResult,
    hash_result: HashResult,
    secret_key: Optional[bytes] = None,
) -> ManifestVerificationResult:
    """Verify observed export properties against a trusted manifest.

    Args:
        manifest_data_or_path: Path to manifest JSON file or loaded dict.
        file_inspection: Intake inspection results.
        compression_validation: Decompression integrity results.
        parsing_result: Streaming parser results.
        hash_result: Cryptographic hashes.
        secret_key: Optional key to verify manifest HMAC signature.

    Returns:
        ManifestVerificationResult with granular checks and overall verdict.
    """
    checks: List[ManifestCheckDetail] = []
    limitations: List[str] = []

    # 1. Load and validate manifest
    if isinstance(manifest_data_or_path, (str, Path)):
        p = Path(manifest_data_or_path).resolve()
        if not p.exists():
            return ManifestVerificationResult(
                overall_status=VerificationStatus.FAIL,
                manifest_provenance=ManifestProvenance.UNKNOWN,
                checks=[ManifestCheckDetail(
                    field_name="manifest_file",
                    status=VerificationStatus.FAIL,
                    expected=str(p),
                    observed="MISSING",
                    message="Specified manifest file does not exist on disk."
                )],
                limitations=["Cannot verify integrity without manifest file."]
            )
        with open(p, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    else:
        manifest = manifest_data_or_path

    try:
        validate_manifest_dict(manifest)
    except Exception as e:
        return ManifestVerificationResult(
            overall_status=VerificationStatus.FAIL,
            manifest_provenance=ManifestProvenance.UNKNOWN,
            checks=[ManifestCheckDetail(
                field_name="manifest_schema",
                status=VerificationStatus.FAIL,
                expected="Valid Version 1.0 Schema",
                observed="INVALID",
                message=f"Manifest schema validation failure: {e}"
            )],
            limitations=["Manifest syntax or version rejected."]
        )

    # 2. Establish Provenance
    provenance = evaluate_provenance(manifest.get("trusted_reference_status", "UNKNOWN"))
    provenance_warning = None

    if provenance == ManifestProvenance.OBSERVATIONAL_POST_HOC:
        provenance_warning = (
            "CAUTION: Manifest was marked as OBSERVATIONAL (generated after-the-fact). "
            "Matching this manifest confirms file identity but DOES NOT prove original source database completeness."
        )
        limitations.append(provenance_warning)
    elif provenance == ManifestProvenance.UNKNOWN:
        provenance_warning = "Manifest provenance is UNKNOWN. Claims of source completeness cannot be substantiated."
        limitations.append(provenance_warning)

    # Optional signature check
    if secret_key:
        sig_valid = verify_manifest_hmac_signature(manifest, secret_key)
        checks.append(ManifestCheckDetail(
            field_name="manifest_signature",
            status=VerificationStatus.PASS if sig_valid else VerificationStatus.FAIL,
            expected="Valid HMAC Signature",
            observed="MATCH" if sig_valid else "MISMATCH",
            message="HMAC cryptographic seal verified successfully." if sig_valid else "Manifest cryptographic signature mismatch or missing key."
        ))

    # 3. Row Count Check
    expected_rows = manifest.get("expected_row_count")
    observed_rows = parsing_result.record_count
    if expected_rows is not None:
        if observed_rows == expected_rows:
            checks.append(ManifestCheckDetail(
                field_name="row_count",
                status=VerificationStatus.PASS,
                expected=expected_rows,
                observed=observed_rows,
                message=f"Row count matches manifest exactly ({observed_rows:,} records)."
            ))
        else:
            checks.append(ManifestCheckDetail(
                field_name="row_count",
                status=VerificationStatus.FAIL,
                expected=expected_rows,
                observed=observed_rows,
                message=f"Row count mismatch! Manifest expected {expected_rows:,}, but observed {observed_rows:,}."
            ))
    else:
        checks.append(ManifestCheckDetail(
            field_name="row_count",
            status=VerificationStatus.INCONCLUSIVE,
            expected=None,
            observed=observed_rows,
            message="Manifest does not declare expected_row_count."
        ))

    # 4. Decompressed Stream Hash Check
    expected_uncompressed_sha = manifest.get("uncompressed_sha256")
    observed_uncompressed_sha = hash_result.decompressed_sha256 or compression_validation.sha256_decompressed
    if expected_uncompressed_sha:
        if observed_uncompressed_sha and observed_uncompressed_sha.lower() == expected_uncompressed_sha.lower():
            checks.append(ManifestCheckDetail(
                field_name="uncompressed_sha256",
                status=VerificationStatus.PASS,
                expected=expected_uncompressed_sha,
                observed=observed_uncompressed_sha,
                message="Decompressed byte stream SHA-256 matches manifest exactly."
            ))
        else:
            checks.append(ManifestCheckDetail(
                field_name="uncompressed_sha256",
                status=VerificationStatus.FAIL,
                expected=expected_uncompressed_sha,
                observed=observed_uncompressed_sha,
                message="Decompressed byte stream SHA-256 mismatch! Content has been altered."
            ))
    else:
        checks.append(ManifestCheckDetail(
            field_name="uncompressed_sha256",
            status=VerificationStatus.INCONCLUSIVE,
            expected=None,
            observed=observed_uncompressed_sha,
            message="Manifest did not declare uncompressed_sha256."
        ))

    # 5. Compressed File Hash Check (if present in manifest)
    expected_comp_sha = manifest.get("compressed_sha256")
    observed_comp_sha = file_inspection.sha256_compressed
    if expected_comp_sha:
        if observed_comp_sha and observed_comp_sha.lower() == expected_comp_sha.lower():
            checks.append(ManifestCheckDetail(
                field_name="compressed_sha256",
                status=VerificationStatus.PASS,
                expected=expected_comp_sha,
                observed=observed_comp_sha,
                message="Compressed file byte hash matches manifest."
            ))
        else:
            checks.append(ManifestCheckDetail(
                field_name="compressed_sha256",
                status=VerificationStatus.WARNING,
                expected=expected_comp_sha,
                observed=observed_comp_sha,
                message="Compressed file hash differs. (Note: Decompression settings or timestamps may alter compressed bytes while uncompressed data remains identical)."
            ))

    # 6. Schema Fingerprint Check
    expected_schema = manifest.get("schema_fingerprint")
    observed_schema = parsing_result.schema_fingerprint
    if expected_schema:
        if observed_schema == expected_schema:
            checks.append(ManifestCheckDetail(
                field_name="schema_fingerprint",
                status=VerificationStatus.PASS,
                expected=expected_schema,
                observed=observed_schema,
                message="Table schema fingerprint matches manifest."
            ))
        else:
            checks.append(ManifestCheckDetail(
                field_name="schema_fingerprint",
                status=VerificationStatus.FAIL,
                expected=expected_schema,
                observed=observed_schema,
                message="Schema structure mismatch! Columns or data types have changed."
            ))

    # 7. Chunk Hashes Check
    manifest_chunks = manifest.get("chunk_hashes", [])
    observed_chunks = hash_result.chunk_hashes
    if manifest_chunks and observed_chunks:
        mismatched_chunks = []
        compared_count = min(len(manifest_chunks), len(observed_chunks))

        for i in range(compared_count):
            m_hash = manifest_chunks[i].get("sha256")
            o_hash = observed_chunks[i].sha256
            if m_hash.lower() != o_hash.lower():
                mismatched_chunks.append(i)

        if len(manifest_chunks) != len(observed_chunks):
            checks.append(ManifestCheckDetail(
                field_name="chunk_count",
                status=VerificationStatus.FAIL,
                expected=len(manifest_chunks),
                observed=len(observed_chunks),
                message=f"Chunk count mismatch: expected {len(manifest_chunks)} chunks, found {len(observed_chunks)}."
            ))

        if not mismatched_chunks and len(manifest_chunks) == len(observed_chunks):
            checks.append(ManifestCheckDetail(
                field_name="chunk_hashes",
                status=VerificationStatus.PASS,
                expected=f"{len(manifest_chunks)} chunks verified",
                observed=f"{len(observed_chunks)} chunks verified",
                message=f"All {compared_count} chunk SHA-256 digests matched successfully."
            ))
        else:
            checks.append(ManifestCheckDetail(
                field_name="chunk_hashes",
                status=VerificationStatus.FAIL,
                expected="All chunks matching",
                observed=f"Mismatches in chunk indices: {mismatched_chunks[:10]}",
                message=f"Detected {len(mismatched_chunks)} chunk hash mismatches."
            ))

    # Determine overall status
    has_fail = any(c.status == VerificationStatus.FAIL for c in checks)
    has_warning = any(c.status == VerificationStatus.WARNING for c in checks)
    has_inconclusive = any(c.status == VerificationStatus.INCONCLUSIVE for c in checks)

    if has_fail:
        overall_status = VerificationStatus.FAIL
    elif has_warning:
        overall_status = VerificationStatus.WARNING
    elif has_inconclusive:
        overall_status = VerificationStatus.INCONCLUSIVE
    else:
        overall_status = VerificationStatus.PASS

    return ManifestVerificationResult(
        overall_status=overall_status,
        manifest_provenance=provenance,
        checks=checks,
        provenance_warning=provenance_warning,
        limitations=limitations
    )

