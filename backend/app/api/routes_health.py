"""Health check and format capabilities API routes."""

from datetime import datetime, timezone
from fastapi import APIRouter
from backend.app.models.responses import HealthResponse, FormatsResponse

router = APIRouter(tags=["Health & Formats"])


@router.get("/health", response_model=HealthResponse)
def get_health():
    """System health check and runtime status."""
    return HealthResponse(
        status="HEALTHY",
        version="1.0.0",
        system_time_utc=datetime.now(timezone.utc).isoformat(),
        features=[
            "bounded_memory_streaming",
            "physical_container_crc_validation",
            "rfc6962_merkle_tree",
            "multi_granularity_hashing",
            "schema_fingerprinting",
            "explainable_anomaly_rules",
            "sqlite_metadata_repository",
            "reportlab_pdf_generation",
        ]
    )


@router.get("/formats", response_model=FormatsResponse)
def get_supported_formats():
    """List supported compression, data, and hashing capabilities."""
    return FormatsResponse(
        compression_formats=["gzip", "bzip2", "xz", "zstandard", "uncompressed"],
        export_formats=["csv", "jsonl", "sql_dump"],
        max_compressed_upload_mb=500,
        default_chunk_size_kb=64
    )

