"""Script: Create Test Exports and Demonstrations (Demos A to F).

Directly reproduces the official problem statement scenario:
- Baseline export: 100,000 rows.
- Newer export: 130,000 rows (+30%), yet file size is ~20% smaller due to high repetition.
- Truncated stream, logically incomplete stream, matching manifest, tampered content.
"""

import gzip
import json
import os
from pathlib import Path
import shutil
import sys

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dbguard.analyzer import analyze_export
from dbguard.manifest.generator import generate_manifest, save_manifest_to_file
from dbguard.models import ManifestProvenance
from scripts.generate_sample_data import write_compressed_csv

SAMPLE_DIR = Path("sample_data").resolve()
MANIFEST_DIR = Path("manifests").resolve()


def create_all_demos():
    SAMPLE_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 72)
    print(" Generating DBGuard Demonstration and Test Datasets")
    print("=" * 72)

    # ---------------------------------------------------------
    # DEMO A: The Problem Statement Scenario (100k rows vs 130k rows smaller)
    # ---------------------------------------------------------
    path_old = SAMPLE_DIR / "demo_a_baseline_100k.csv.gz"
    path_new = SAMPLE_DIR / "demo_a_repetitive_130k.csv.gz"

    print("\n[1/6] Generating Demo A Baseline (100,000 rows, normal entropy)...")
    size_old = write_compressed_csv(
        path_old,
        row_count=100_000,
        repetitive=False,
        long_text=False,
        seed=101
    )
    print(f"      Baseline compressed size: {size_old:,} bytes")

    print("[2/6] Generating Demo A Newer Export (130,000 rows, repetitive data)...")
    size_new = write_compressed_csv(
        path_new,
        row_count=130_000,
        repetitive=True,
        long_text=False,
        seed=102
    )
    print(f"      Newer export compressed size: {size_new:,} bytes")

    row_pct = ((130_000 - 100_000) / 100_000) * 100.0
    size_pct = ((size_new - size_old) / size_old) * 100.0
    print(f"      >> Confirmed Relationship: Rows +{row_pct:.1f}% | Size {size_pct:.1f}%")

    # ---------------------------------------------------------
    # DEMO B: Deliberately Truncated Compressed Stream
    # ---------------------------------------------------------
    print("\n[3/6] Generating Demo B Truncated Compressed Stream...")
    path_trunc = SAMPLE_DIR / "demo_b_truncated.csv.gz"
    # Take first 45% of the baseline file and truncate without gzip trailer
    with open(path_old, "rb") as f_in:
        raw_bytes = f_in.read()
    trunc_len = int(len(raw_bytes) * 0.45)
    with open(path_trunc, "wb") as f_out:
        f_out.write(raw_bytes[:trunc_len])
    print(f"      Truncated file written: {path_trunc.stat().st_size:,} bytes")

    # ---------------------------------------------------------
    # DEMO C: Logically Incomplete but Valid Compressed Export
    # ---------------------------------------------------------
    print("\n[4/6] Generating Demo C Logically Incomplete (85k rows vs 100k manifest)...")
    path_inc = SAMPLE_DIR / "demo_c_incomplete_85k.csv.gz"
    write_compressed_csv(
        path_inc,
        row_count=85_000,
        repetitive=False,
        seed=103
    )
    # Create manifest expecting 100,000 rows
    rep_100k = analyze_export(path_old)
    man_c = generate_manifest(
        export_id="EXP-DAILY-BACKUP-100K",
        source_identifier="production_transactions_tbl",
        export_format="csv",
        compression_format="gzip",
        schema_fingerprint=rep_100k.parsing_result.schema_fingerprint,
        expected_row_count=100_000,  # Pipeline expected 100k!
        uncompressed_size_bytes=rep_100k.compression_validation.decompressed_bytes,
        uncompressed_sha256=rep_100k.hash_result.decompressed_sha256,
        compressed_size_bytes=rep_100k.file_inspection.file_size_bytes,
        compressed_sha256=rep_100k.file_inspection.sha256_compressed,
        chunk_hashes=rep_100k.hash_result.chunk_hashes,
        trusted_reference_status=ManifestProvenance.TRUSTED_EXPORT_PIPELINE
    )
    save_manifest_to_file(man_c, MANIFEST_DIR / "demo_c_incomplete_85k.manifest.json")
    print("      Incomplete export and trusted pipeline manifest created.")

    # ---------------------------------------------------------
    # DEMO E: Matching Trusted Manifest (25,000 rows)
    # ---------------------------------------------------------
    print("\n[5/6] Generating Demo E Matching Trusted Export (25,000 rows)...")
    path_match = SAMPLE_DIR / "demo_e_matching_25k.csv.gz"
    write_compressed_csv(
        path_match,
        row_count=25_000,
        repetitive=False,
        seed=200
    )
    rep_match = analyze_export(path_match)
    man_e = generate_manifest(
        export_id="EXP-VERIFIED-25K",
        source_identifier="accounts_master_tbl",
        export_format="csv",
        compression_format="gzip",
        schema_fingerprint=rep_match.parsing_result.schema_fingerprint,
        expected_row_count=25_000,
        uncompressed_size_bytes=rep_match.compression_validation.decompressed_bytes,
        uncompressed_sha256=rep_match.hash_result.decompressed_sha256,
        compressed_size_bytes=rep_match.file_inspection.file_size_bytes,
        compressed_sha256=rep_match.file_inspection.sha256_compressed,
        chunk_hashes=rep_match.hash_result.chunk_hashes,
        trusted_reference_status=ManifestProvenance.TRUSTED_EXPORT_PIPELINE
    )
    save_manifest_to_file(man_e, MANIFEST_DIR / "demo_e_matching_25k.manifest.json")
    print("      Matching export and manifest created.")

    # ---------------------------------------------------------
    # DEMO F: Modified Content (Tampered)
    # ---------------------------------------------------------
    print("\n[6/6] Generating Demo F Tampered Content...")
    path_tampered = SAMPLE_DIR / "demo_f_tampered_25k.csv.gz"
    # Same row count (25,000) but different seed/data values
    write_compressed_csv(
        path_tampered,
        row_count=25_000,
        repetitive=False,
        seed=999
    )
    # We test it against demo_e's manifest to show checksum mismatch!
    shutil.copy(MANIFEST_DIR / "demo_e_matching_25k.manifest.json", MANIFEST_DIR / "demo_f_tampered_25k.manifest.json")
    print("      Tampered export created (paired with original manifest).")

    # Additional edge cases: malformed csv records
    path_malformed = SAMPLE_DIR / "test_malformed.csv.gz"
    with open(path_malformed, "wb") as rf:
        with gzip.GzipFile(fileobj=rf, mode="wb") as gf:
            content = (
                "id,name,value\n"
                "1,Alice,100\n"
                "2,Bob,200,EXTRA_COLUMN_HERE\n"  # Column count mismatch
                '3,"Charlie"UnclosedQuotes,300\n'
                "4,David,400\n"
            )
            gf.write(content.encode("utf-8"))

    print("\n" + "=" * 72)
    print(" Test Exports and Manifests generated successfully in:")
    print(f"  • Data:     {SAMPLE_DIR}")
    print(f"  • Manifest: {MANIFEST_DIR}")
    print("=" * 72)


if __name__ == "__main__":
    create_all_demos()
