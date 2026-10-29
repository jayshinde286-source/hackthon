"""Export comparison API routes."""

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from backend.app.database.connection import get_db
from backend.app.database.tables import DBComparison
from backend.app.models.responses import ComparisonSummary
from dbguard.analyzer import analyze_export
from dbguard.analysis.comparison import compare_exports
from dbguard.models import ExportMetrics

router = APIRouter(prefix="/comparisons", tags=["Comparison"])

TEMP_DIR = Path(tempfile.gettempdir()) / "dbguard_comparisons"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@router.post("", response_model=ComparisonSummary)
async def create_comparison(
    old_file: UploadFile = File(...),
    new_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Execute streaming comparison between an earlier baseline export and a newer export."""
    path_old = TEMP_DIR / f"old_{uuid.uuid4().hex}_{old_file.filename}"
    path_new = TEMP_DIR / f"new_{uuid.uuid4().hex}_{new_file.filename}"

    try:
        with open(path_old, "wb") as f_o:
            while chunk := await old_file.read(65_536):
                f_o.write(chunk)

        with open(path_new, "wb") as f_n:
            while chunk := await new_file.read(65_536):
                f_n.write(chunk)

        rep_old = analyze_export(path_old, filename_override=old_file.filename)
        rep_new = analyze_export(
            path_new,
            filename_override=new_file.filename,
            comparison_baseline_metrics=ExportMetrics(
                compressed_size_bytes=rep_old.file_inspection.file_size_bytes,
                decompressed_size_bytes=rep_old.compression_validation.decompressed_bytes,
                row_count=rep_old.parsing_result.record_count,
                compression_ratio=rep_old.compression_validation.expansion_ratio,
                bytes_per_row=(rep_old.compression_validation.decompressed_bytes / max(1, rep_old.parsing_result.record_count)),
                schema_fingerprint=rep_old.parsing_result.schema_fingerprint,
                column_count=rep_old.parsing_result.column_count,
                malformed_count=rep_old.parsing_result.malformed_record_count
            ),
            comparison_baseline_header=rep_old.parsing_result.header
        )

        p_old = rep_old.parsing_result
        p_new = rep_new.parsing_result
        fi_old = rep_old.file_inspection
        fi_new = rep_new.file_inspection

        row_pct = round(((p_new.record_count - p_old.record_count) / max(1, p_old.record_count)) * 100.0, 2)
        comp_pct = round(((fi_new.file_size_bytes - fi_old.file_size_bytes) / max(1, fi_old.file_size_bytes)) * 100.0, 2)
        decomp_pct = round(((rep_new.compression_validation.decompressed_bytes - rep_old.compression_validation.decompressed_bytes) / max(1, rep_old.compression_validation.decompressed_bytes)) * 100.0, 2)
        ratio_old = round(rep_old.compression_validation.decompressed_bytes / max(1, fi_old.file_size_bytes), 2)
        ratio_new = round(rep_new.compression_validation.decompressed_bytes / max(1, fi_new.file_size_bytes), 2)
        bpr_old = round(rep_old.compression_validation.decompressed_bytes / max(1, p_old.record_count), 2)
        bpr_new = round(rep_new.compression_validation.decompressed_bytes / max(1, p_new.record_count), 2)

        schema_match = (p_old.schema_fingerprint == p_new.schema_fingerprint)
        anomaly_flags = []

        if row_pct > 0 and comp_pct < 0:
            anomaly_flags.append(
                f"Row count increased (+{row_pct:.1f}%), yet compressed file size decreased ({comp_pct:.1f}%). "
                "Higher repetition or NULL density produced higher dictionary compression efficiency."
            )

        if not schema_match:
            anomaly_flags.append("Schema structure mismatch detected between baseline and current exports.")

        diffs = [
            {"metric": "Row Count", "old": p_old.record_count, "new": p_new.record_count, "change_pct": row_pct},
            {"metric": "Compressed Bytes", "old": fi_old.file_size_bytes, "new": fi_new.file_size_bytes, "change_pct": comp_pct},
            {"metric": "Decompressed Bytes", "old": rep_old.compression_validation.decompressed_bytes, "new": rep_new.compression_validation.decompressed_bytes, "change_pct": decomp_pct},
            {"metric": "Compression Ratio", "old": ratio_old, "new": ratio_new, "change_pct": round(((ratio_new - ratio_old)/max(1, ratio_old))*100, 2)},
            {"metric": "Bytes Per Row", "old": bpr_old, "new": bpr_new, "change_pct": round(((bpr_new - bpr_old)/max(1, bpr_old))*100, 2)},
        ]

        summary_verdict = (
            f"Compared {p_old.record_count:,} rows ({fi_old.file_size_bytes:,} B) -> "
            f"{p_new.record_count:,} rows ({fi_new.file_size_bytes:,} B). "
            f"{'Anomalies flagged for review.' if anomaly_flags else 'Metrics consistent with expected operational growth.'}"
        )

        cmp_id = f"CMP-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

        db_cmp = DBComparison(
            id=cmp_id,
            previous_filename=old_file.filename,
            current_filename=new_file.filename,
            row_count_change_pct=row_pct,
            compressed_size_change_pct=comp_pct,
            decompressed_size_change_pct=decomp_pct,
            compression_ratio_old=ratio_old,
            compression_ratio_new=ratio_new,
            bytes_per_row_old=bpr_old,
            bytes_per_row_new=bpr_new,
            schema_match=schema_match,
            summary_verdict=summary_verdict,
            created_at=datetime.now(timezone.utc),
            full_comparison_json=json.dumps({"diffs": diffs, "anomaly_flags": anomaly_flags})
        )
        db.add(db_cmp)
        db.commit()

        return ComparisonSummary(
            id=cmp_id,
            previous_filename=old_file.filename,
            current_filename=new_file.filename,
            row_count_change_pct=row_pct,
            compressed_size_change_pct=comp_pct,
            decompressed_size_change_pct=decomp_pct,
            compression_ratio_old=ratio_old,
            compression_ratio_new=ratio_new,
            bytes_per_row_old=bpr_old,
            bytes_per_row_new=bpr_new,
            schema_match=schema_match,
            summary_verdict=summary_verdict,
            created_at=datetime.now(timezone.utc).isoformat(),
            diffs=diffs,
            anomaly_flags=anomaly_flags
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")
    finally:
        for p in (path_old, path_new):
            if p.exists():
                try:
                    p.unlink()
                except Exception:
                    pass

