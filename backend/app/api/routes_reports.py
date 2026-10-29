"""Report generation and download API routes (PDF, JSON, CSV)."""

import json
from pathlib import Path
import tempfile

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.tables import DBAnalysis
from dbguard.models import (
    AnalysisReport,
    Anomaly,
    AnomalySeverity,
    CompressionFormat,
    CompressionValidationResult,
    ExportFormat,
    FileInspection,
    HashResult,
    ManifestCheckDetail,
    ManifestProvenance,
    ManifestVerificationResult,
    ParsingResult,
    RecoveryAssessment,
    RecoveryClassification,
    VerificationStatus,
)
from dbguard.reporting.csv_report import generate_csv_report
from dbguard.reporting.json_report import generate_json_report
from dbguard.reporting.pdf_report import generate_pdf_report

router = APIRouter(prefix="/analyses", tags=["Reports"])

REPORT_TEMP_DIR = Path(tempfile.gettempdir()) / "dbguard_generated_reports"
REPORT_TEMP_DIR.mkdir(parents=True, exist_ok=True)


def _reconstruct_report(d: dict) -> AnalysisReport:
    """Reconstruct typed AnalysisReport dataclass from stored JSON dictionary."""
    fi_d = d["file_inspection"]
    fi = FileInspection(
        path=fi_d["path"],
        filename=fi_d["filename"],
        file_size_bytes=fi_d["file_size_bytes"],
        detected_compression=CompressionFormat(fi_d["detected_compression"]),
        sha256_compressed=fi_d["sha256_compressed"],
        is_empty=fi_d["is_empty"],
        is_valid_header=fi_d["is_valid_header"],
        header_hex=fi_d["header_hex"],
        inspection_notes=fi_d.get("inspection_notes", [])
    )

    cv_d = d["compression_validation"]
    cv = CompressionValidationResult(
        status=VerificationStatus(cv_d["status"]),
        format=CompressionFormat(cv_d["format"]),
        compressed_bytes_read=cv_d["compressed_bytes_read"],
        decompressed_bytes=cv_d["decompressed_bytes"],
        expansion_ratio=cv_d["expansion_ratio"],
        sha256_decompressed=cv_d["sha256_decompressed"],
        is_truncated=cv_d["is_truncated"],
        crc_or_trailer_valid=cv_d.get("crc_or_trailer_valid"),
        error_message=cv_d.get("error_message"),
        limitations=cv_d.get("limitations", [])
    )

    pr_d = d["parsing_result"]
    pr = ParsingResult(
        status=VerificationStatus(pr_d["status"]),
        format=ExportFormat(pr_d["format"]),
        header=pr_d["header"],
        column_count=pr_d["column_count"],
        record_count=pr_d["record_count"],
        malformed_record_count=pr_d["malformed_record_count"],
        empty_value_count=pr_d["empty_value_count"],
        schema_fingerprint=pr_d["schema_fingerprint"]
    )

    hr_d = d["hash_result"]
    hr = HashResult(
        compressed_sha256=hr_d["compressed_sha256"],
        decompressed_sha256=hr_d["decompressed_sha256"],
        merkle_root=hr_d.get("merkle_root")
    )

    mv = None
    if d.get("manifest_verification"):
        mv_d = d["manifest_verification"]
        mv_checks = [
            ManifestCheckDetail(
                field_name=c["field_name"],
                status=VerificationStatus(c["status"]),
                expected=c["expected"],
                observed=c["observed"],
                message=c["message"]
            ) for c in mv_d.get("checks", [])
        ]
        mv = ManifestVerificationResult(
            overall_status=VerificationStatus(mv_d["overall_status"]),
            manifest_provenance=ManifestProvenance(mv_d["manifest_provenance"]),
            checks=mv_checks,
            provenance_warning=mv_d.get("provenance_warning")
        )

    anoms = []
    for a_d in d.get("anomalies", []):
        anoms.append(Anomaly(
            rule_id=a_d["rule_id"],
            severity=AnomalySeverity(a_d["severity"]),
            metric_name=a_d["metric_name"],
            observed_value=a_d["observed_value"],
            expected_or_baseline=a_d["expected_or_baseline"],
            threshold=a_d["threshold"],
            explanation=a_d["explanation"],
            recommendation=a_d["recommendation"],
            evidence_ref=a_d["evidence_ref"],
            confidence_limitations=a_d["confidence_limitations"]
        ))

    ra_d = d["recovery_assessment"]
    ra = RecoveryAssessment(
        classification=RecoveryClassification(ra_d["classification"]),
        summary=ra_d["summary"],
        verified_properties=ra_d.get("verified_properties", []),
        unverified_or_inconclusive=ra_d.get("unverified_or_inconclusive", []),
        failures=ra_d.get("failures", []),
        recoverable_record_estimate=ra_d.get("recoverable_record_estimate", 0),
        recommended_actions=ra_d.get("recommended_actions", []),
        evidence_needed_for_full_claim=ra_d.get("evidence_needed_for_full_claim", [])
    )

    return AnalysisReport(
        report_id=d["report_id"],
        tool_name="DBGuard",
        tool_version="1.0.0",
        generated_at_utc=d["generated_at_utc"],
        file_inspection=fi,
        compression_validation=cv,
        parsing_result=pr,
        hash_result=hr,
        manifest_verification=mv,
        anomalies=anoms,
        recovery_assessment=ra,
        execution_duration_sec=d["execution_duration_sec"]
    )


@router.get("/{analysis_id}/report")
def download_report(
    analysis_id: str,
    format: str = Query("pdf", pattern="^(pdf|json|csv)$"),
    db: Session = Depends(get_db)
):
    """Generate and download audit reports in PDF, JSON, or CSV format."""
    record = db.query(DBAnalysis).filter(DBAnalysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis record not found.")

    data_dict = json.loads(record.full_report_json)
    report = _reconstruct_report(data_dict)

    if format == "json":
        json_str = generate_json_report(report)
        return Response(
            content=json_str,
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="{analysis_id}_report.json"'}
        )
    elif format == "csv":
        csv_str = generate_csv_report(report)
        return Response(
            content=csv_str,
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{analysis_id}_summary.csv"'}
        )
    else:
        # PDF
        pdf_path = REPORT_TEMP_DIR / f"{analysis_id}.pdf"
        generate_pdf_report(report, pdf_path)
        return FileResponse(
            path=str(pdf_path),
            media_type="application/pdf",
            filename=f"{analysis_id}_integrity_report.pdf"
        )
