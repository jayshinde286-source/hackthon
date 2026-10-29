"""Module 8: Integrity Manifest Generator.

Constructs versioned JSON manifest documents. Explicitly differentiates manifests
produced by trusted export pipelines from observational manifests generated after-the-fact.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from dbguard.hashing.chunk_hash import ChunkHashEntry
from dbguard.manifest.schema import CURRENT_MANIFEST_VERSION, validate_manifest_dict
from dbguard.manifest.trust import compute_manifest_hmac_signature
from dbguard.models import ManifestProvenance


def generate_manifest(
    export_id: str,
    source_identifier: str,
    export_format: str,
    compression_format: str,
    schema_fingerprint: str,
    expected_row_count: int,
    uncompressed_size_bytes: int,
    uncompressed_sha256: str,
    compressed_size_bytes: Optional[int] = None,
    compressed_sha256: Optional[str] = None,
    chunk_hashes: Optional[List[Union[ChunkHashEntry, Dict[str, Any]]]] = None,
    trusted_reference_status: ManifestProvenance = ManifestProvenance.TRUSTED_EXPORT_PIPELINE,
    secret_key: Optional[bytes] = None,
    generation_method: str = "dbguard_manifest_generator",
    producer_version: str = "1.0.0",
) -> Dict[str, Any]:
    """Create a structured, validated integrity manifest dictionary.

    Args:
        export_id: Unique identifier for the database export.
        source_identifier: Database or table identifier (non-sensitive).
        export_format: Format (csv, jsonl, sql_dump).
        compression_format: Compression type (gzip, bz2, xz, etc.).
        schema_fingerprint: SHA-256 fingerprint of table schema.
        expected_row_count: Verified row count.
        uncompressed_size_bytes: Total decompressed bytes.
        uncompressed_sha256: SHA-256 hash over decompressed stream.
        compressed_size_bytes: Exact byte size of compressed file.
        compressed_sha256: SHA-256 hash of compressed file.
        chunk_hashes: List of ChunkHashEntry objects or dicts.
        trusted_reference_status: Provenance status (pipeline, independent, or observational).
        secret_key: Optional secret key for HMAC sealing.
        generation_method: Origin generator description.
        producer_version: Tool version string.

    Returns:
        Validated manifest dictionary.
    """
    is_observational = (trusted_reference_status == ManifestProvenance.OBSERVATIONAL_POST_HOC)

    # Format chunks
    formatted_chunks: List[Dict[str, Any]] = []
    if chunk_hashes:
        for ch in chunk_hashes:
            if isinstance(ch, ChunkHashEntry):
                formatted_chunks.append({
                    "index": ch.index,
                    "start_byte": ch.start_byte,
                    "end_byte": ch.end_byte,
                    "length_bytes": ch.length_bytes,
                    "sha256": ch.sha256,
                    "record_count": ch.record_count
                })
            elif isinstance(ch, dict):
                formatted_chunks.append(ch)

    now_utc = datetime.now(timezone.utc).isoformat()

    manifest: Dict[str, Any] = {
        "manifest_version": CURRENT_MANIFEST_VERSION,
        "export_id": export_id,
        "export_timestamp_utc": now_utc,
        "source_identifier": source_identifier,
        "export_format": str(export_format),
        "compression_format": str(compression_format),
        "schema_fingerprint": schema_fingerprint,
        "expected_row_count": int(expected_row_count),
        "uncompressed_size_bytes": int(uncompressed_size_bytes),
        "uncompressed_sha256": uncompressed_sha256,
        "chunking_scheme": "fixed_bytes_1MB" if formatted_chunks else "none",
        "chunk_hashes": formatted_chunks,
        "record_counting_convention": "data_rows_excluding_header",
        "generation_method": generation_method,
        "producer_version": producer_version,
        "trusted_reference_status": trusted_reference_status.value,
        "is_observational": is_observational,
    }

    if compressed_size_bytes is not None:
        manifest["compressed_size_bytes"] = int(compressed_size_bytes)
    if compressed_sha256 is not None:
        manifest["compressed_sha256"] = compressed_sha256

    if is_observational:
        manifest["provenance_notice"] = (
            "NOTICE: This manifest was generated post-hoc from an existing export file. "
            "It establishes an identity reference for this specific file, but does NOT "
            "prove that the export pipeline successfully captured all source records from the database."
        )

    if secret_key:
        manifest["signature"] = compute_manifest_hmac_signature(manifest, secret_key)

    validate_manifest_dict(manifest)
    return manifest


def save_manifest_to_file(manifest: Dict[str, Any], filepath: Union[str, Path]) -> Path:
    """Save manifest to a JSON file."""
    p = Path(filepath).expanduser().resolve()
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return p

