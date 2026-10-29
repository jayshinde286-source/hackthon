"""Analysis execution, history, and detailed evidence API routes."""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.tables import DBAnalysis, DBAnomaly, DBIntegrityCheck
from backend.app.models.responses import (
    AnalysisDetail,
    AnalysisSummary,
    AnomalyItem,
    IntegrityCheckItem,
    RecoveryAssessmentItem,
)
from dbguard.analyzer import analyze_export
from dbguard.models import ExportFormat, VerificationStatus

router = APIRouter(prefix="/analyses", tags=["Analysis"])

TEMP_DIR = Path(tempfile.gettempdir()) / "dbguard_uploads"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


def _analysis_to_detail(analysis: DBAnalysis) -> AnalysisDetail:
    """Helper to convert ORM DBAnalysis into Pydantic AnalysisDetail."""
    report_dict = json.loads(analysis.full_report_json)

    checks = [
        IntegrityCheckItem(
            category=c.category,
            check_name=c.check_name,
            status=c.status,
            observed_value=c.observed_value,
            expected_value=c.expected_value,
            explanation=c.explanation,
            evidence_reference=c.evidence_reference
        ) for c in analysis.checks
    ]

    anomalies = [
        AnomalyItem(
            rule_id=a.rule_id,
            severity=a.severity,
            metric_name=a.metric_name,
            observed_value=a.observed_value,
            expected_value=a.expected_value,
            explanation=a.explanation,
            recommendation=a.recommendation
        ) for a in analysis.anomalies
    ]

    rec = report_dict.get("recovery_assessment", {})
    recovery_item = RecoveryAssessmentItem(
        classification=analysis.recovery_assessment,
        summary=analysis.recovery_summary,
        verified_properties=rec.get("verified_properties", []),
        unverified_or_inconclusive=rec.get("unverified_or_inconclusive", []),
        failures=rec.get("failures", []),
        recoverable_record_estimate=rec.get("recoverable_record_estimate", 0),
        recommended_actions=rec.get("recommended_actions", []),
        evidence_needed_for_full_claim=rec.get("evidence_needed_for_full_claim", [])
    )

    summary = AnalysisSummary(
        id=analysis.id,
        original_filename=analysis.original_filename,
        file_size_bytes=analysis.file_size_bytes,
        compressed_size_bytes=analysis.compressed_size_bytes,
        decompressed_size_bytes=analysis.decompressed_size_bytes,
        row_count=analysis.row_count,
        column_count=analysis.column_count,
        compression_format=analysis.compression_format,
        data_format=analysis.data_format,
        compressed_sha256=analysis.compressed_sha256,
        decompressed_sha256=analysis.decompressed_sha256,
        schema_fingerprint=analysis.schema_fingerprint,
        analysis_status=analysis.analysis_status,
        recovery_assessment=analysis.recovery_assessment,
        recovery_summary=analysis.recovery_summary,
        execution_duration_sec=analysis.execution_duration_sec,
        created_at=analysis.created_at.isoformat() if analysis.created_at else datetime.now(timezone.utc).isoformat()
    )

    return AnalysisDetail(
        summary=summary,
        checks=checks,
        anomalies=anomalies,
        recovery=recovery_item,
        full_report=report_dict
    )


@router.post("", response_model=AnalysisDetail, status_code=status.HTTP_201_CREATED)
async def create_analysis(
    file: UploadFile = File(...),
    manifest_file: Optional[UploadFile] = File(None),
    data_format: Optional[str] = Form(None),
    secret_key: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """Execute streaming analysis on an uploaded database export and store metadata in SQLite."""
    # Write incoming file stream into safe temporary path
    safe_name = f"{uuid.uuid4().hex}_{file.filename}"
    temp_file_path = TEMP_DIR / safe_name

    try:
        with open(temp_file_path, "wb") as f_out:
            while chunk := await file.read(65_536):
                f_out.write(chunk)

        # Parse manifest if provided
        manifest_data = None
        if manifest_file:
            content = await manifest_file.read()
            manifest_data = json.loads(content.decode("utf-8"))

        resolved_fmt = None
        if data_format and data_format.lower() in ("csv", "jsonl", "sql_dump"):
            resolved_fmt = ExportFormat(data_format.lower())

        s_key = secret_key.encode("utf-8") if secret_key else None

        # Execute single-pass streaming engine
        report = analyze_export(
            file_path_or_buffer=temp_file_path,
            filename_override=file.filename,
            data_format=resolved_fmt,
            manifest_path_or_dict=manifest_data,
            secret_key=s_key
        )

        # Create database record
        db_analysis = DBAnalysis(
            id=report.report_id,
            original_filename=file.filename,
            file_size_bytes=report.file_inspection.file_size_bytes,
            compressed_size_bytes=report.compression_validation.compressed_bytes_read,
            decompressed_size_bytes=report.compression_validation.decompressed_bytes,
            row_count=report.parsing_result.record_count,
            column_count=report.parsing_result.column_count,
            compression_format=report.compression_validation.format.value,
            data_format=report.parsing_result.format.value,
            compressed_sha256=report.file_inspection.sha256_compressed,
            decompressed_sha256=report.hash_result.decompressed_sha256,
            schema_fingerprint=report.parsing_result.schema_fingerprint,
            analysis_status=report.compression_validation.status.value,
            recovery_assessment=report.recovery_assessment.classification.value,
            recovery_summary=report.recovery_assessment.summary,
            execution_duration_sec=report.execution_duration_sec,
            created_at=datetime.now(timezone.utc),
            full_report_json=json.dumps(report.to_dict())
        )

        # Save checks
        checks_to_add = []
        checks_to_add.append(DBIntegrityCheck(
            analysis_id=report.report_id,
            category="Physical Stream",
            check_name="Container Integrity & CRC",
            status=report.compression_validation.status.value,
            observed_value=f"CRC Valid: {report.compression_validation.crc_or_trailer_valid}",
            expected_value="Valid Header and Trailer",
            explanation=f"Stream format {report.compression_validation.format.value.upper()} decompressor verification",
            evidence_reference=f"Read {report.compression_validation.compressed_bytes_read:,} compressed bytes"
        ))
        checks_to_add.append(DBIntegrityCheck(
            analysis_id=report.report_id,
            category="Record Parsing",
            check_name="Column Structure Uniformity",
            status="PASS" if report.parsing_result.malformed_record_count == 0 else "WARNING",
            observed_value=f"{report.parsing_result.malformed_record_count} malformed rows",
            expected_value="0 malformed rows",
            explanation=f"Consistent {report.parsing_result.column_count} columns across {report.parsing_result.record_count:,} rows",
            evidence_reference="Streaming parser line validation"
        ))

        if report.manifest_verification:
            for c in report.manifest_verification.checks:
                checks_to_add.append(DBIntegrityCheck(
                    analysis_id=report.report_id,
                    category="Manifest Verification",
                    check_name=f"Manifest: {c.field_name}",
                    status=c.status.value,
                    observed_value=str(c.observed)[:100],
                    expected_value=str(c.expected)[:100],
                    explanation=c.message,
                    evidence_reference=f"Provenance: {report.manifest_verification.manifest_provenance.value}"
                ))

        db_analysis.checks = checks_to_add

        # Save anomalies
        anoms_to_add = []
        for a in report.anomalies:
            anoms_to_add.append(DBAnomaly(
                analysis_id=report.report_id,
                rule_id=a.rule_id,
                severity=a.severity.value,
                metric_name=a.metric_name,
                observed_value=str(a.observed_value),
                expected_value=str(a.expected_or_baseline),
                explanation=a.explanation,
                recommendation=a.recommendation
            ))
        db_analysis.anomalies = anoms_to_add

        db.add(db_analysis)
        db.commit()
        db.refresh(db_analysis)

        return _analysis_to_detail(db_analysis)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")
    finally:
        if temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception:
                pass


@router.get("", response_model=List[AnalysisSummary])
def list_analyses(db: Session = Depends(get_db)):
    """Retrieve history of all analyzed exports stored in the SQLite repository."""
    records = db.query(DBAnalysis).order_by(DBAnalysis.created_at.desc()).all()
    summaries = []
    for r in records:
        summaries.append(AnalysisSummary(
            id=r.id,
            original_filename=r.original_filename,
            file_size_bytes=r.file_size_bytes,
            compressed_size_bytes=r.compressed_size_bytes,
            decompressed_size_bytes=r.decompressed_size_bytes,
            row_count=r.row_count,
            column_count=r.column_count,
            compression_format=r.compression_format,
            data_format=r.data_format,
            compressed_sha256=r.compressed_sha256,
            decompressed_sha256=r.decompressed_sha256,
            schema_fingerprint=r.schema_fingerprint,
            analysis_status=r.analysis_status,
            recovery_assessment=r.recovery_assessment,
            recovery_summary=r.recovery_summary,
            execution_duration_sec=r.execution_duration_sec,
            created_at=r.created_at.isoformat() if r.created_at else ""
        ))
    return summaries


@router.get("/{analysis_id}", response_model=AnalysisDetail)
def get_analysis_detail(analysis_id: str, db: Session = Depends(get_db)):
    """Retrieve complete analysis details, checks, anomalies, and recovery assessment."""
    record = db.query(DBAnalysis).filter(DBAnalysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail=f"Analysis '{analysis_id}' not found.")
    return _analysis_to_detail(record)


@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_analysis(analysis_id: str, db: Session = Depends(get_db)):
    """Delete an analysis record and its associated checks/anomalies from SQLite."""
    record = db.query(DBAnalysis).filter(DBAnalysis.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found.")
    db.delete(record)
    db.commit()
    return None

