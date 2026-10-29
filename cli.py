"""DBGuard Command-Line Interface (CLI).

Provides non-destructive inspection, unified streaming analysis, export comparison,
manifest generation and verification, and report production from the terminal.
"""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Optional

from dbguard.analyzer import analyze_export
from dbguard.file_inspector import inspect_file
from dbguard.manifest.generator import generate_manifest, save_manifest_to_file
from dbguard.manifest.verifier import verify_manifest
from dbguard.models import (
    AnalysisReport,
    ExportFormat,
    ExportMetrics,
    ManifestProvenance,
    RecoveryClassification,
    VerificationStatus,
)
from dbguard.reporting.csv_report import generate_csv_report
from dbguard.reporting.json_report import generate_json_report
from dbguard.reporting.pdf_report import generate_pdf_report


def _print_header(title: str):
    print("=" * 72)
    print(f" DBGuard: {title}")
    print("=" * 72)


def cmd_inspect(args: argparse.Namespace) -> int:
    """Intake inspection of file header and compressed hash."""
    _print_header("File Intake Inspection")
    try:
        insp = inspect_file(args.file)
        print(f"File Path:            {insp.path}")
        print(f"Filename:             {insp.filename}")
        print(f"Compressed Size:      {insp.file_size_bytes:,} bytes")
        print(f"Detected Format:      {insp.detected_compression.value.upper()}")
        print(f"Header Valid:         {insp.is_valid_header}")
        print(f"Header Hex:           {insp.header_hex}")
        print(f"Compressed SHA-256:   {insp.sha256_compressed}")
        if insp.inspection_notes:
            print("Notes:")
            for n in insp.inspection_notes:
                print(f"  • {n}")

        if args.json:
            print("\nJSON Output:")
            print(json.dumps({
                "path": insp.path,
                "file_size_bytes": insp.file_size_bytes,
                "detected_compression": insp.detected_compression.value,
                "sha256_compressed": insp.sha256_compressed,
                "is_empty": insp.is_empty,
                "is_valid_header": insp.is_valid_header,
            }, indent=2))
        return 0
    except Exception as e:
        print(f"ERROR: Inspection failed: {e}", file=sys.stderr)
        return 1


def cmd_analyze(args: argparse.Namespace) -> int:
    """Run full streaming analysis on an export file."""
    _print_header("Streaming Export Analysis")
    try:
        fmt = ExportFormat(args.format) if args.format else None
        secret_key = args.key.encode("utf-8") if args.key else None

        print(f"Analyzing: {args.file} ...")
        report = analyze_export(
            file_path_or_buffer=args.file,
            data_format=fmt,
            manifest_path_or_dict=args.manifest,
            secret_key=secret_key
        )

        rec = report.recovery_assessment
        print("\n" + "-" * 72)
        print(f"RECOVERY VERDICT: {rec.classification.value}")
        print("-" * 72)
        print(f"Summary:              {rec.summary}")
        print(f"Compression Format:   {report.compression_validation.format.value.upper()} (Status: {report.compression_validation.status.value})")
        print(f"Compressed Size:      {report.file_inspection.file_size_bytes:,} bytes")
        print(f"Decompressed Size:    {report.compression_validation.decompressed_bytes:,} bytes")
        print(f"Expansion Ratio:      {report.compression_validation.expansion_ratio:.2f}x")
        print(f"Rows Parsed:          {report.parsing_result.record_count:,}")
        print(f"Columns:              {report.parsing_result.column_count}")
        print(f"Malformed Records:    {report.parsing_result.malformed_record_count:,}")
        print(f"Decompressed SHA-256: {report.hash_result.decompressed_sha256}")
        print(f"Merkle Root (1MB):    {report.hash_result.merkle_root or 'N/A'}")
        print(f"Execution Duration:   {report.execution_duration_sec:.3f} seconds")

        if report.manifest_verification:
            mv = report.manifest_verification
            print(f"\nManifest Verification: {mv.overall_status.value} (Provenance: {mv.manifest_provenance.value})")
            for c in mv.checks:
                print(f"  [{c.status.value:4}] {c.field_name:<20}: {c.message}")

        if report.anomalies:
            print(f"\nDetected Anomalies ({len(report.anomalies)}):")
            for a in report.anomalies:
                print(f"  [{a.severity.value:<8}] {a.rule_id}: {a.explanation}")

        # Optional report generation
        if args.output_pdf:
            pdf_path = generate_pdf_report(report, args.output_pdf)
            print(f"\n[+] PDF Report generated at: {pdf_path}")
        if args.output_json:
            json_path = Path(args.output_json)
            generate_json_report(report, json_path)
            print(f"[+] JSON Report generated at: {json_path}")
        if args.output_csv:
            csv_path = Path(args.output_csv)
            generate_csv_report(report, csv_path)
            print(f"[+] CSV Report generated at: {csv_path}")

        if args.json:
            print("\nJSON Report Output:")
            print(generate_json_report(report))

        if rec.classification == RecoveryClassification.INTEGRITY_FAILURE:
            return 1
        elif rec.classification in (RecoveryClassification.RECOVERY_POSSIBLE_WITH_ERRORS, RecoveryClassification.INCONCLUSIVE):
            return 2
        return 0

    except Exception as e:
        print(f"ERROR: Analysis aborted: {e}", file=sys.stderr)
        return 1


def cmd_compare(args: argparse.Namespace) -> int:
    """Compare two exports and evaluate physical and structural shifts."""
    _print_header("Export Comparative Analysis")
    try:
        print(f"Analyzing baseline (OLD): {args.old} ...")
        rep_old = analyze_export(args.old)

        print(f"Analyzing current  (NEW): {args.new} ...")
        rep_new = analyze_export(
            args.new,
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

        old_p = rep_old.parsing_result
        new_p = rep_new.parsing_result
        old_fi = rep_old.file_inspection
        new_fi = rep_new.file_inspection

        row_pct = ((new_p.record_count - old_p.record_count) / max(1, old_p.record_count)) * 100.0
        size_pct = ((new_fi.file_size_bytes - old_fi.file_size_bytes) / max(1, old_fi.file_size_bytes)) * 100.0
        ratio_old = rep_old.compression_validation.decompressed_bytes / max(1, old_fi.file_size_bytes)
        ratio_new = rep_new.compression_validation.decompressed_bytes / max(1, new_fi.file_size_bytes)

        print("\n" + "-" * 72)
        print(f"{'METRIC':<28} | {'BASELINE (OLD)':<18} | {'CURRENT (NEW)':<18} | {'DIFF'}")
        print("-" * 72)
        print(f"{'Row Count':<28} | {old_p.record_count:<18,d} | {new_p.record_count:<18,d} | {row_pct:+.1f}%")
        print(f"{'Compressed Size (bytes)':<28} | {old_fi.file_size_bytes:<18,d} | {new_fi.file_size_bytes:<18,d} | {size_pct:+.1f}%")
        print(f"{'Decompressed Size (bytes)':<28} | {rep_old.compression_validation.decompressed_bytes:<18,d} | {rep_new.compression_validation.decompressed_bytes:<18,d} |")
        print(f"{'Compression Ratio':<28} | {ratio_old:<18.2f} | {ratio_new:<18.2f} |")
        print(f"{'Schema Fingerprint Match':<28} | {str(old_p.schema_fingerprint == new_p.schema_fingerprint)}")
        print("-" * 72)

        # Highlight Problem Statement Condition
        if row_pct > 0 and size_pct < 0:
            print("\n>> ANOMALY DETECTED (Problem Statement Scenario):")
            print(f"   Export row count increased (+{row_pct:.1f}%), yet compressed file size decreased ({size_pct:.1f}%).")
            print("   Explanation: Compression dictionary efficiency, higher string repetition, or NULL frequencies")
            print("   can legitimately produce this result without data corruption.")

        if rep_new.anomalies:
            print("\nAnomalies in Current Export:")
            for a in rep_new.anomalies:
                print(f"  • [{a.severity.value}] {a.explanation}")

        return 0
    except Exception as e:
        print(f"ERROR: Comparison failed: {e}", file=sys.stderr)
        return 1


def cmd_generate_manifest(args: argparse.Namespace) -> int:
    """Generate an integrity manifest for an export file."""
    _print_header("Integrity Manifest Generator")
    try:
        report = analyze_export(args.file)
        if report.compression_validation.status == VerificationStatus.FAIL:
            print("ERROR: Cannot generate manifest for corrupted or unreadable export file.", file=sys.stderr)
            return 1

        provenance = (
            ManifestProvenance.TRUSTED_EXPORT_PIPELINE if args.trusted else ManifestProvenance.OBSERVATIONAL_POST_HOC
        )
        secret_key = args.key.encode("utf-8") if args.key else None

        manifest = generate_manifest(
            export_id=f"EXP-{Path(args.file).stem}",
            source_identifier=args.source_id or Path(args.file).stem,
            export_format=report.parsing_result.format.value,
            compression_format=report.compression_validation.format.value,
            schema_fingerprint=report.parsing_result.schema_fingerprint,
            expected_row_count=report.parsing_result.record_count,
            uncompressed_size_bytes=report.compression_validation.decompressed_bytes,
            uncompressed_sha256=report.hash_result.decompressed_sha256,
            compressed_size_bytes=report.file_inspection.file_size_bytes,
            compressed_sha256=report.file_inspection.sha256_compressed,
            chunk_hashes=report.hash_result.chunk_hashes,
            trusted_reference_status=provenance,
            secret_key=secret_key
        )

        out_path = save_manifest_to_file(manifest, args.output)
        print(f"[+] Manifest successfully generated and saved to: {out_path}")
        print(f"    Expected Rows:     {manifest['expected_row_count']:,}")
        print(f"    Decompressed SHA:  {manifest['uncompressed_sha256']}")
        print(f"    Provenance:        {manifest['trusted_reference_status']}")
        if not args.trusted:
            print("\nWARNING: Manifest created as 'OBSERVATIONAL_POST_HOC' because it was generated after-the-fact.")
            print("         It proves file identity but does not prove original source completeness.")
        return 0

    except Exception as e:
        print(f"ERROR: Manifest generation failed: {e}", file=sys.stderr)
        return 1


def cmd_verify_manifest(args: argparse.Namespace) -> int:
    """Verify an export against a trusted manifest."""
    _print_header("Manifest Verification")
    try:
        secret_key = args.key.encode("utf-8") if args.key else None
        report = analyze_export(
            args.file,
            manifest_path_or_dict=args.manifest,
            secret_key=secret_key
        )

        mv = report.manifest_verification
        if not mv:
            print("ERROR: Manifest verification was not performed.", file=sys.stderr)
            return 1

        print(f"Manifest File:         {args.manifest}")
        print(f"Manifest Provenance:   {mv.manifest_provenance.value}")
        print(f"Overall Concordance:   {mv.overall_status.value}")
        print("\nIndividual Checks:")
        for c in mv.checks:
            print(f"  [{c.status.value:<4}] {c.field_name:<22}: {c.message}")

        if mv.provenance_warning:
            print(f"\nProvenance Warning:\n  {mv.provenance_warning}")

        return 0 if mv.overall_status == VerificationStatus.PASS else 1
    except Exception as e:
        print(f"ERROR: Manifest verification failed: {e}", file=sys.stderr)
        return 1


def main():
    parser = argparse.ArgumentParser(
        prog="dbguard",
        description="DBGuard: Compressed Database Export Integrity Analyzer (Without Full Database Restoration)"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # inspect
    p_inspect = subparsers.add_parser("inspect", help="Intake inspection of file header and compressed hash")
    p_inspect.add_argument("--file", required=True, help="Path to export file")
    p_inspect.add_argument("--json", action="store_true", help="Output JSON")
    p_inspect.set_defaults(func=cmd_inspect)

    # analyze
    p_analyze = subparsers.add_parser("analyze", help="Perform streaming integrity and recovery analysis")
    p_analyze.add_argument("--file", required=True, help="Path to export file")
    p_analyze.add_argument("--format", choices=["csv", "jsonl", "sql_dump"], help="Explicit data format")
    p_analyze.add_argument("--manifest", help="Optional path to trusted integrity manifest")
    p_analyze.add_argument("--key", help="Optional HMAC secret key for manifest signature")
    p_analyze.add_argument("--output-pdf", help="Save PDF report to path")
    p_analyze.add_argument("--output-json", help="Save JSON report to path")
    p_analyze.add_argument("--output-csv", help="Save CSV report to path")
    p_analyze.add_argument("--json", action="store_true", help="Output full JSON report to stdout")
    p_analyze.set_defaults(func=cmd_analyze)

    # compare
    p_compare = subparsers.add_parser("compare", help="Compare an earlier baseline export with a newer export")
    p_compare.add_argument("--old", required=True, help="Baseline (earlier) export file")
    p_compare.add_argument("--new", required=True, help="Current (newer) export file")
    p_compare.add_argument("--json", action="store_true", help="Output JSON")
    p_compare.set_defaults(func=cmd_compare)

    # generate-manifest
    p_gen = subparsers.add_parser("generate-manifest", help="Generate an integrity manifest for an export")
    p_gen.add_argument("--file", required=True, help="Export file")
    p_gen.add_argument("--output", required=True, help="Output manifest JSON path")
    p_gen.add_argument("--source-id", help="Source database or table identifier")
    p_gen.add_argument("--trusted", action="store_true", help="Mark as TRUSTED_EXPORT_PIPELINE instead of OBSERVATIONAL_POST_HOC")
    p_gen.add_argument("--key", help="Optional HMAC secret key to cryptographically seal the manifest")
    p_gen.set_defaults(func=cmd_generate_manifest)

    # verify-manifest
    p_ver = subparsers.add_parser("verify-manifest", help="Verify export against a trusted manifest")
    p_ver.add_argument("--file", required=True, help="Export file")
    p_ver.add_argument("--manifest", required=True, help="Manifest JSON file")
    p_ver.add_argument("--key", help="Optional HMAC secret key for signature verification")
    p_ver.set_defaults(func=cmd_verify_manifest)

    args = parser.parse_args()
    sys.exit(args.func(args))


if __name__ == "__main__":
    main()

