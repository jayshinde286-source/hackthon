"""Manifest provenance, trust level evaluation, and cryptographic sealing."""

import hmac
import hashlib
import json
from typing import Dict, Any, Optional
from dbguard.models import ManifestProvenance


def evaluate_provenance(raw_status: str) -> ManifestProvenance:
    """Normalize and validate manifest trust status string."""
    try:
        return ManifestProvenance(raw_status)
    except ValueError:
        return ManifestProvenance.UNKNOWN


def compute_manifest_hmac_signature(manifest_dict: Dict[str, Any], secret_key: bytes) -> str:
    """Compute HMAC-SHA256 signature over canonicalized JSON manifest payload (excluding signature)."""
    clean_copy = {k: v for k, v in manifest_dict.items() if k != "signature"}
    canonical_json = json.dumps(clean_copy, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hmac.new(secret_key, canonical_json, hashlib.sha256).hexdigest()


def verify_manifest_hmac_signature(manifest_dict: Dict[str, Any], secret_key: bytes) -> bool:
    """Verify that the manifest's embedded signature matches the canonical content."""
    sig = manifest_dict.get("signature")
    if not sig:
        return False
    expected_sig = compute_manifest_hmac_signature(manifest_dict, secret_key)
    return hmac.compare_digest(sig, expected_sig)

