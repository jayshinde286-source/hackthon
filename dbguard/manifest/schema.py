"""Module 8: Trusted Integrity Manifest Schema and Validation."""

import json
from typing import Dict, Any, List
from dbguard.exceptions import ManifestError

CURRENT_MANIFEST_VERSION = "1.0"

REQUIRED_FIELDS = [
    "manifest_version",
    "export_id",
    "export_timestamp_utc",
    "source_identifier",
    "export_format",
    "compression_format",
    "schema_fingerprint",
    "expected_row_count",
    "uncompressed_size_bytes",
    "uncompressed_sha256",
    "chunking_scheme",
    "chunk_hashes",
    "record_counting_convention",
    "generation_method",
    "producer_version",
    "trusted_reference_status",
]


def validate_manifest_dict(data: Dict[str, Any]) -> None:
    """Validate a parsed integrity manifest dictionary against the DBGuard schema.

    Raises:
        ManifestError: If required fields are missing or values violate schema constraints.
    """
    if not isinstance(data, dict):
        raise ManifestError("Manifest root must be a JSON object/dictionary.")

    version = data.get("manifest_version")
    if not version:
        raise ManifestError("Manifest missing 'manifest_version'.")
    if version != CURRENT_MANIFEST_VERSION:
        raise ManifestError(
            f"Unsupported manifest version '{version}'. Expected version '{CURRENT_MANIFEST_VERSION}'."
        )

    missing = [f for f in REQUIRED_FIELDS if f not in data]
    if missing:
        raise ManifestError(f"Manifest is missing required field(s): {', '.join(missing)}")

    # Type constraints
    if not isinstance(data["expected_row_count"], int) or data["expected_row_count"] < 0:
        raise ManifestError("Field 'expected_row_count' must be a non-negative integer.")

    if not isinstance(data["uncompressed_size_bytes"], int) or data["uncompressed_size_bytes"] < 0:
        raise ManifestError("Field 'uncompressed_size_bytes' must be a non-negative integer.")

    if not isinstance(data["uncompressed_sha256"], str) or len(data["uncompressed_sha256"]) != 64:
        raise ManifestError("Field 'uncompressed_sha256' must be a 64-character hexadecimal SHA-256 digest.")

    if not isinstance(data["chunk_hashes"], list):
        raise ManifestError("Field 'chunk_hashes' must be a list of chunk descriptors.")

