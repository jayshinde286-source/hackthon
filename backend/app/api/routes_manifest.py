"""Manifest validation, generation, and verification API routes."""

import json
from pathlib import Path
import tempfile
from typing import Any, Dict, Optional
import uuid

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from dbguard.analyzer import analyze_export
from dbguard.manifest.generator import generate_manifest
from dbguard.manifest.schema import validate_manifest_dict
from dbguard.manifest.verifier import verify_manifest
from dbguard.models import ManifestProvenance

router = APIRouter(prefix="/manifests", tags=["Manifests"])

TEMP_DIR = Path(tempfile.gettempdir()) / "dbguard_manifests"
TEMP_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/validate")
async def validate_manifest_schema(file: UploadFile = File(...)):
    """Validate that an uploaded JSON manifest satisfies DBGuard Schema Version 1.0."""
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        validate_manifest_dict(data)
        return {
            "status": "VALID",
            "message": "Manifest complies with DBGuard Manifest Schema Version 1.0",
            "manifest": data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Manifest schema validation failure: {str(e)}")


@router.post("/generate")
async def create_manifest_for_export(
    file: UploadFile = File(...),
    source_identifier: str = Form("production_table"),
    is_trusted: bool = Form(False),
    secret_key: Optional[str] = Form(None)
):
    """Generate a versioned manifest from an uploaded export file."""
    temp_path = TEMP_DIR / f"{uuid.uuid4().hex}_{file.filename}"
    try:
        with open(temp_path, "wb") as f_out:
            while chunk := await file.read(65_536):
                f_out.write(chunk)

        report = analyze_export(temp_path, filename_override=file.filename)
        prov = ManifestProvenance.TRUSTED_EXPORT_PIPELINE if is_trusted else ManifestProvenance.OBSERVATIONAL_POST_HOC
        s_bytes = secret_key.encode("utf-8") if secret_key else None

        manifest = generate_manifest(
            export_id=f"EXP-{Path(file.filename).stem}",
            source_identifier=source_identifier,
            export_format=report.parsing_result.format.value,
            compression_format=report.compression_validation.format.value,
            schema_fingerprint=report.parsing_result.schema_fingerprint,
            expected_row_count=report.parsing_result.record_count,
            uncompressed_size_bytes=report.compression_validation.decompressed_bytes,
            uncompressed_sha256=report.hash_result.decompressed_sha256,
            compressed_size_bytes=report.file_inspection.file_size_bytes,
            compressed_sha256=report.file_inspection.sha256_compressed,
            chunk_hashes=report.hash_result.chunk_hashes,
            trusted_reference_status=prov,
            secret_key=s_bytes
        )

        return {
            "status": "SUCCESS",
            "provenance": prov.value,
            "manifest": manifest
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manifest generation failed: {str(e)}")
    finally:
        if temp_path.exists():
            try:
                temp_path.unlink()
            except Exception:
                pass

