"""DBGuard Core Engine: Algorithm A — Unified Streaming Export Analysis.

Orchestrates file inspection, bounded streaming decompression, concurrent cryptographic
stream and chunk hashing, streaming record parsing, manifest verification,
anomaly detection, and recovery assessment in a single bounded-memory pass.
"""

from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import time
from typing import Any, BinaryIO, Callable, Dict, List, Optional, Union
import uuid

from dbguard.analysis.anomalies import detect_anomalies
from dbguard.analysis.comparison import compare_exports
from dbguard.analysis.recovery_assessment import assess_recovery_feasibility
from dbguard.analysis.statistics import calculate_bytes_per_row, calculate_compression_ratio
from dbguard.compression.integrity import validate_compression_integrity
from dbguard.compression.streaming import StreamingDecompressor
from dbguard.exceptions import (
    CorruptedStreamError,
    ResourceLimitExceededError,
    TruncatedStreamError,
    UnsupportedFormatError,
)
from dbguard.file_inspector import inspect_file
from dbguard.hashing.chunk_hash import ChunkHasher
from dbguard.hashing.merkle import MerkleTree
from dbguard.hashing.stream_hash import StreamHasher
from dbguard.manifest.verifier import verify_manifest
from dbguard.models import (
    AnalysisReport,
    CompressionFormat,
    CompressionValidationResult,
    ExportComparison,
    ExportFormat,
    ExportMetrics,
    FileInspection,
    HashResult,
    ManifestVerificationResult,
    ParsingResult,
    RecoveryAssessment,
    VerificationStatus,
)
from dbguard.parsers.csv_parser import parse_csv_stream
from dbguard.parsers.jsonl_parser import parse_jsonl_stream
from dbguard.parsers.sql_parser import parse_sql_dump_stream


def detect_export_format_from_name(filename: str) -> ExportFormat:
    """Infer data format from filename extension."""
    fn = filename.lower()
    # Strip common compression suffixes
    for comp_ext in (".gz", ".bz2", ".xz", ".zst", ".tar"):
        if fn.endswith(comp_ext):
            fn = fn[:-len(comp_ext)]

    if fn.endswith(".csv") or fn.endswith(".tsv"):
        return ExportFormat.CSV
    elif fn.endswith(".jsonl") or fn.endswith(".ndjson"):
        return ExportFormat.JSONL
    elif fn.endswith(".sql") or fn.endswith(".dump"):
        return ExportFormat.SQL_DUMP
    return ExportFormat.CSV  # Default to CSV


def analyze_export(
    file_path_or_buffer: Union[str, Path, BinaryIO],
    filename_override: Optional[str] = None,
    data_format: Optional[ExportFormat] = None,
    manifest_path_or_dict: Optional[Union[str, Path, Dict[str, Any]]] = None,
    comparison_baseline_metrics: Optional[ExportMetrics] = None,
    comparison_baseline_header: Optional[List[str]] = None,
    historical_metrics: Optional[List[ExportMetrics]] = None,
    chunk_size_bytes: int = 65_536,
    chunk_verify_bytes: int = 1_048_576,
    max_decompressed_size: int = 5_368_709_120,
    max_expansion_ratio: float = 100.0,
    secret_key: Optional[bytes] = None,
    progress_callback: Optional[Callable[[int, Optional[int]], None]] = None,
) -> AnalysisReport:
    """Execute Algorithm A: Unified Streaming Export Analysis.

    Args:
        file_path_or_buffer: Path to file or binary stream.
        filename_override: Display name if passing a stream.
        data_format: Format (CSV, JSONL, SQL_DUMP). If None, inferred from filename.
        manifest_path_or_dict: Optional manifest path or dictionary.
        comparison_baseline_metrics: Optional past export metrics for comparative diffs.
        comparison_baseline_header: Optional past header for schema comparison.
        historical_metrics: Optional list of past metrics for MAD/IQR anomaly detection.
        chunk_size_bytes: Streaming buffer size.
        chunk_verify_bytes: Granular chunk hash size (default 1MB).
        max_decompressed_size: Max uncompressed bytes before raising security limit.
        max_expansion_ratio: Max expansion ratio before raising security limit.
        secret_key: Optional secret key to verify HMAC-sealed manifests.
        progress_callback: Optional callback receiving (bytes_read, total_bytes).

    Returns:
        Comprehensive AnalysisReport object.
    """
    start_time = time.perf_counter()
    report_id = f"DBG-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6]}"

    # Step 1: Intake File Inspection
    inspection = inspect_file(
        file_path_or_buffer=file_path_or_buffer,
        filename_override=filename_override,
    )

    resolved_format = data_format or detect_export_format_from_name(inspection.filename)

    # Short-circuit on empty or unsupported header
    if inspection.is_empty or not inspection.is_valid_header:
        comp_res = CompressionValidationResult(
            status=VerificationStatus.FAIL if not inspection.is_empty else VerificationStatus.INCONCLUSIVE,
            format=inspection.detected_compression,
            compressed_bytes_read=0,
            decompressed_bytes=0,
            expansion_ratio=0.0,
            sha256_decompressed="",
            is_truncated=False,
            crc_or_trailer_valid=False,
            error_message="Empty file or unrecognized compression header.",
            limitations=["Cannot decompress empty or unrecognized file."]
        )
        parse_res = ParsingResult(
            status=VerificationStatus.INCONCLUSIVE,
            format=resolved_format,
            header=[],
            column_count=0,
            record_count=0,
            malformed_record_count=0,
            empty_value_count=0,
            schema_fingerprint="",
            column_stats=[],
            errors=[],
            total_errors_count=0,
            bytes_consumed=0
        )
        hash_res = HashResult(
            compressed_sha256=inspection.sha256_compressed,
            decompressed_sha256="",
            chunk_hashes=[],
            merkle_root=""
        )
        anomalies = detect_anomalies(inspection, parse_res, hash_res)
        rec_assessment = assess_recovery_feasibility(inspection, comp_res, parse_res, None, anomalies)

        return AnalysisReport(
            report_id=report_id,
            tool_name="DBGuard",
            tool_version="1.0.0",
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
            file_inspection=inspection,
            compression_validation=comp_res,
            parsing_result=parse_res,
            hash_result=hash_res,
            manifest_verification=None,
            anomalies=anomalies,
            recovery_assessment=rec_assessment,
            execution_duration_sec=round(time.perf_counter() - start_time, 4),
            config_snapshot={"chunk_size_bytes": chunk_size_bytes, "max_expansion_ratio": max_expansion_ratio}
        )

    # Step 2: Initialize Decompressor, Hashers, and Streaming Tapper
    decompressor = StreamingDecompressor(
        stream_or_path=file_path_or_buffer,
        format_type=inspection.detected_compression,
        chunk_size=chunk_size_bytes,
        max_decompressed_size=max_decompressed_size,
        max_expansion_ratio=max_expansion_ratio,
    )

    stream_hasher = StreamHasher()
    chunk_hasher = ChunkHasher(chunk_boundary_bytes=chunk_verify_bytes)
    decompressed_bytes_count = 0
    is_truncated = False
    crc_valid = None
    decomp_status = VerificationStatus.PASS
    decomp_error: Optional[str] = None

    def tapped_chunk_stream():
        nonlocal decompressed_bytes_count, is_truncated, crc_valid, decomp_status, decomp_error
        try:
            for chunk in decompressor.stream_chunks():
                stream_hasher.update(chunk)
                chunk_hasher.update(chunk)
                decompressed_bytes_count += len(chunk)
                if progress_callback:
                    progress_callback(decompressor.compressed_bytes_read, inspection.file_size_bytes)
                yield chunk
            crc_valid = True
        except TruncatedStreamError as e:
            decomp_status = VerificationStatus.FAIL
            is_truncated = True
            crc_valid = False
            decomp_error = f"Stream truncated: {e}"
        except CorruptedStreamError as e:
            decomp_status = VerificationStatus.FAIL
            crc_valid = False
            decomp_error = f"Stream corrupted: {e}"
        except ResourceLimitExceededError as e:
            decomp_status = VerificationStatus.FAIL
            decomp_error = f"Security limit violated: {e}"
        except Exception as e:
            decomp_status = VerificationStatus.FAIL
            decomp_error = f"Unexpected decompression failure: {e}"

    # Step 3: Stream directly into the chosen Format Parser
    chunk_gen = tapped_chunk_stream()
    if resolved_format == ExportFormat.CSV:
        parse_res = parse_csv_stream(chunk_gen)
    elif resolved_format == ExportFormat.JSONL:
        parse_res = parse_jsonl_stream(chunk_gen)
    elif resolved_format == ExportFormat.SQL_DUMP:
        parse_res = parse_sql_dump_stream(chunk_gen)
    else:
        parse_res = parse_csv_stream(chunk_gen)

    # Step 4: Finalize Chunk Hashes and Merkle Tree
    final_chunks = chunk_hasher.finalize()
    merkle_tree = MerkleTree([bytes.fromhex(c.sha256) for c in final_chunks], are_already_leaf_hashed=False)

    decompressed_sha = stream_hasher.hexdigest()
    comp_size = inspection.file_size_bytes or decompressor.compressed_bytes_read or 1
    expansion_ratio = round(decompressed_bytes_count / max(1, comp_size), 4)

    comp_res = CompressionValidationResult(
        status=decomp_status,
        format=inspection.detected_compression,
        compressed_bytes_read=comp_size,
        decompressed_bytes=decompressed_bytes_count,
        expansion_ratio=expansion_ratio,
        sha256_decompressed=decompressed_sha if decomp_status == VerificationStatus.PASS else "",
        is_truncated=is_truncated,
        crc_or_trailer_valid=crc_valid,
        error_message=decomp_error,
        limitations=[
            "Passing physical stream integrity proves the compression container is structurally intact and decodable.",
            "It does NOT prove that the database export command included all records from the source table."
        ]
    )

    hash_res = HashResult(
        compressed_sha256=inspection.sha256_compressed,
        decompressed_sha256=decompressed_sha,
        chunk_hashes=final_chunks,
        merkle_root=merkle_tree.root_hex,
        canonical_record_hash=None
    )

    # Step 5: Verify Trusted Manifest if provided
    manifest_verification: Optional[ManifestVerificationResult] = None
    if manifest_path_or_dict:
        manifest_verification = verify_manifest(
            manifest_data_or_path=manifest_path_or_dict,
            file_inspection=inspection,
            compression_validation=comp_res,
            parsing_result=parse_res,
            hash_result=hash_res,
            secret_key=secret_key
        )

    # Step 6: Perform Export Comparison if baseline metrics provided
    comparison: Optional[ExportComparison] = None
    current_metrics = ExportMetrics(
        compressed_size_bytes=comp_size,
        decompressed_size_bytes=decompressed_bytes_count,
        row_count=parse_res.record_count,
        compression_ratio=calculate_compression_ratio(decompressed_bytes_count, comp_size),
        bytes_per_row=calculate_bytes_per_row(decompressed_bytes_count, parse_res.record_count),
        schema_fingerprint=parse_res.schema_fingerprint,
        column_count=parse_res.column_count,
        malformed_count=parse_res.malformed_record_count
    )

    if comparison_baseline_metrics:
        comparison = compare_exports(
            old_metrics=comparison_baseline_metrics,
            new_metrics=current_metrics,
            old_header=comparison_baseline_header,
            new_header=parse_res.header
        )

    # Step 7: Detect Anomalies (Algorithm C)
    anomalies = detect_anomalies(
        file_inspection=inspection,
        parsing_result=parse_res,
        hash_result=hash_res,
        manifest_verification=manifest_verification,
        comparison=comparison,
        historical_metrics=historical_metrics
    )

    # Step 8: Recovery Assessment (Algorithm E)
    rec_assessment = assess_recovery_feasibility(
        file_inspection=inspection,
        compression_validation=comp_res,
        parsing_result=parse_res,
        manifest_verification=manifest_verification,
        anomalies=anomalies
    )

    duration = round(time.perf_counter() - start_time, 4)

    return AnalysisReport(
        report_id=report_id,
        tool_name="DBGuard",
        tool_version="1.0.0",
        generated_at_utc=datetime.now(timezone.utc).isoformat(),
        file_inspection=inspection,
        compression_validation=comp_res,
        parsing_result=parse_res,
        hash_result=hash_res,
        manifest_verification=manifest_verification,
        anomalies=anomalies,
        recovery_assessment=rec_assessment,
        execution_duration_sec=duration,
        config_snapshot={
            "chunk_size_bytes": chunk_size_bytes,
            "chunk_verify_bytes": chunk_verify_bytes,
            "max_decompressed_size": max_decompressed_size,
            "max_expansion_ratio": max_expansion_ratio,
            "data_format": resolved_format.value
        }
    )

