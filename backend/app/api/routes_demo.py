"""Demonstration scenarios API routes for instant viva/presentation evaluation."""

from datetime import datetime, timezone
import json
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.api.routes_analysis import _analysis_to_detail
from backend.app.database.connection import get_db
from backend.app.database.tables import DBAnalysis, DBAnomaly, DBIntegrityCheck
from backend.app.models.responses import AnalysisDetail
from dbguard.analyzer import analyze_export

router = APIRouter(prefix="/demo", tags=["Demonstration Scenarios"])

SAMPLE_DIR = Path(__file__).resolve().parent.parent.parent.parent / "sample_data"
MANIFEST_DIR = Path(__file__).resolve().parent.parent.parent.parent / "manifests"

DEMO_SCENARIOS = {
    "problem_statement": {
        "title": "Problem Statement Anomaly: 130k Rows (~385 KB, Smaller despite +30% rows)",
        "file": "demo_a_repetitive_130k.csv.gz",
        "manifest": None,
        "description": "Demonstrates the official problem scenario where 130,000 rows compress to a much smaller size than 100,000 rows due to high string repetition and dictionary efficiency."
    },
    "baseline_100k": {
        "title": "Baseline Export: 100,000 Rows (~3.09 MB)",
        "file": "demo_a_baseline_100k.csv.gz",
        "manifest": None,
        "description": "Standard baseline export with diverse entropy used for comparative analysis."
    },
    "truncated": {
        "title": "Physical Corruption: Truncated Gzip Stream",
        "file": "demo_b_truncated.csv.gz",
        "manifest": None,
        "description": "Truncated gzip stream missing trailer; fails physical container integrity."
    },
    "incomplete": {
        "title": "Logical Incompleteness: 85k Rows vs 100k Manifest",
        "file": "demo_c_incomplete_85k.csv.gz",
        "manifest": "demo_c_incomplete_85k.manifest.json",
        "description": "Valid gzip stream with clean decompression, but fails trusted pipeline manifest row count."
    },
    "matching": {
        "title": "Fully Verified: 25k Rows with Pipeline Manifest",
        "file": "demo_e_matching_25k.csv.gz",
        "manifest": "demo_e_matching_25k.manifest.json",
        "description": "Clean stream where compression, row count, stream hash, schema, and chunk hashes all pass."
    },
    "tampered": {
        "title": "Cryptographic Mismatch: Tampered Record Content",
        "file": "demo_f_tampered_25k.csv.gz",
        "manifest": "demo_f_tampered_25k.manifest.json",
        "description": "Row count matches manifest, but uncompressed SHA-256 and chunk hashes reveal data modification."
    }
}


@router.get("/scenarios")
def list_demo_scenarios():
    """List all available pre-generated demonstration scenarios."""
    return [
        {
            "id": k,
            "title": v["title"],
            "description": v["description"],
            "file": v["file"],
            "has_manifest": v["manifest"] is not None
        }
        for k, v in DEMO_SCENARIOS.items()
    ]


@router.post("/run/{scenario_id}", response_model=AnalysisDetail)
def run_demo_scenario(scenario_id: str, db: Session = Depends(get_db)):
    """Run an official demonstration scenario through the real engine and save to SQLite."""
    scenario = DEMO_SCENARIOS.get(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Demo scenario not found.")

    target_file = SAMPLE_DIR / scenario["file"]
    if not target_file.exists():
        raise HTTPException(status_code=500, detail="Demo file does not exist on disk.")

    manifest_path = (MANIFEST_DIR / scenario["manifest"]) if scenario["manifest"] else None

    report = analyze_export(
        file_path_or_buffer=target_file,
        filename_override=scenario["file"],
        manifest_path_or_dict=manifest_path
    )

    # Save to SQLite
    db_analysis = DBAnalysis(
        id=report.report_id,
        original_filename=scenario["file"],
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

    checks_to_add = [
        DBIntegrityCheck(
            analysis_id=report.report_id,
            category="Physical Stream",
            check_name="Container Integrity & CRC",
            status=report.compression_validation.status.value,
            observed_value=f"CRC Valid: {report.compression_validation.crc_or_trailer_valid}",
            expected_value="Valid Header and Trailer",
            explanation=f"Stream format {report.compression_validation.format.value.upper()} decompressor verification",
            evidence_reference=f"Read {report.compression_validation.compressed_bytes_read:,} compressed bytes"
        ),
        DBIntegrityCheck(
            analysis_id=report.report_id,
            category="Record Parsing",
            check_name="Column Structure Uniformity",
            status="PASS" if report.parsing_result.malformed_record_count == 0 else "WARNING",
            observed_value=f"{report.parsing_result.malformed_record_count} malformed rows",
            expected_value="0 malformed rows",
            explanation=f"Consistent {report.parsing_result.column_count} columns across {report.parsing_result.record_count:,} rows",
            evidence_reference="Streaming parser line validation"
        )
    ]

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

