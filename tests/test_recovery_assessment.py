"""Tests for Module 11: Recovery Assessment Feasibility Engine."""

import pytest
from dbguard.analysis.recovery_assessment import assess_recovery_feasibility
from dbguard.models import (
    CompressionFormat,
    CompressionValidationResult,
    ExportFormat,
    FileInspection,
    ManifestProvenance,
    ManifestVerificationResult,
    ParsingResult,
    RecoveryClassification,
    VerificationStatus,
)


def test_recovery_assessment_classifications():
    """Test 34: Exact classification logic for all standardized recovery verdicts."""
    fi = FileInspection("/tmp/f.gz", "f.gz", 1000, CompressionFormat.GZIP, "sha", False, True, "1f8b")

    # 1. Physical Failure -> INTEGRITY_FAILURE
    comp_fail = CompressionValidationResult(
        VerificationStatus.FAIL, CompressionFormat.GZIP, 1000, 500, 0.5, "", is_truncated=True, error_message="CRC Error"
    )
    pr = ParsingResult(VerificationStatus.PASS, ExportFormat.CSV, ["id"], 1, 10, 0, 0, "fp", [], [], 0, 500)
    rec1 = assess_recovery_feasibility(fi, comp_fail, pr)
    assert rec1.classification == RecoveryClassification.INTEGRITY_FAILURE

    # 2. Parsing Malformed Records -> RECOVERY_POSSIBLE_WITH_ERRORS
    comp_pass = CompressionValidationResult(
        VerificationStatus.PASS, CompressionFormat.GZIP, 1000, 4000, 4.0, "sha_d", is_truncated=False
    )
    pr_malformed = ParsingResult(
        VerificationStatus.WARNING, ExportFormat.CSV, ["id", "val"], 2, 100, 5, 0, "fp", [], [], 5, 4000
    )
    rec2 = assess_recovery_feasibility(fi, comp_pass, pr_malformed)
    assert rec2.classification == RecoveryClassification.RECOVERY_POSSIBLE_WITH_ERRORS
    assert rec2.recoverable_record_estimate == 95

    # 3. Clean stream, but NO manifest -> LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED
    pr_clean = ParsingResult(VerificationStatus.PASS, ExportFormat.CSV, ["id"], 1, 1000, 0, 0, "fp", [], [], 0, 4000)
    rec3 = assess_recovery_feasibility(fi, comp_pass, pr_clean)
    assert rec3.classification == RecoveryClassification.LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED
    assert any("completeness" in u.lower() for u in rec3.unverified_or_inconclusive)

    # 4. Clean stream WITH Trusted Pipeline Manifest -> VERIFIED_WITHIN_SCOPE
    mv_pass = ManifestVerificationResult(
        overall_status=VerificationStatus.PASS,
        manifest_provenance=ManifestProvenance.TRUSTED_EXPORT_PIPELINE,
        checks=[]
    )
    rec4 = assess_recovery_feasibility(fi, comp_pass, pr_clean, manifest_verification=mv_pass)
    assert rec4.classification == RecoveryClassification.VERIFIED_WITHIN_SCOPE

