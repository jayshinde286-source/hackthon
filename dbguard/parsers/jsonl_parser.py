"""Module 5: Streaming JSON Lines Parser.

Reads JSON Lines records one at a time from an uncompressed byte chunk iterator,
tracks key signatures, handles malformed lines safely, and enforces line length limits.
"""

import hashlib
import io
import json
from typing import Iterator, List, Dict, Set, Optional

from dbguard.parsers.stream_adapter import ChunkGeneratorReader
from dbguard.models import (
    ColumnStats,
    ExportFormat,
    ParseErrorDetail,
    ParsingResult,
    VerificationStatus,
)

DEFAULT_MAX_LINE_LENGTH = 10_485_760  # 10 MB per JSON line


def parse_jsonl_stream(
    byte_chunks: Iterator[bytes],
    encoding: str = "utf-8",
    max_line_length: int = DEFAULT_MAX_LINE_LENGTH,
    max_errors_retained: int = 100,
) -> ParsingResult:
    """Parse JSON Lines incrementally without accumulating all records in memory.

    Args:
        byte_chunks: Stream of uncompressed bytes.
        encoding: Text encoding.
        max_line_length: Maximum allowed bytes per individual line.
        max_errors_retained: Max error records to store.

    Returns:
        ParsingResult with record statistics and schema fingerprint.
    """
    raw_reader = ChunkGeneratorReader(byte_chunks)
    text_stream = io.TextIOWrapper(
        io.BufferedReader(raw_reader, buffer_size=65_536),
        encoding=encoding,
        errors="replace"
    )

    record_count = 0
    malformed_count = 0
    empty_value_count = 0
    errors: List[ParseErrorDetail] = []
    observed_keys: Set[str] = set()
    key_type_counts: Dict[str, Dict[str, int]] = {}

    line_num = 0

    for line in text_stream:
        line_num += 1
        line_strip = line.strip()
        if not line_strip:
            continue

        if len(line) > max_line_length:
            malformed_count += 1
            if len(errors) < max_errors_retained:
                errors.append(ParseErrorDetail(
                    line_number=line_num,
                    error_type="LINE_LENGTH_EXCEEDED",
                    message=f"Line {line_num} length ({len(line):,} chars) exceeded limit {max_line_length:,}."
                ))
            continue

        try:
            data = json.loads(line_strip)
            if not isinstance(data, dict):
                malformed_count += 1
                if len(errors) < max_errors_retained:
                    errors.append(ParseErrorDetail(
                        line_number=line_num,
                        error_type="NOT_A_JSON_OBJECT",
                        message=f"Line {line_num} contains valid JSON but is not an object/dictionary."
                    ))
                continue

            record_count += 1
            for k, v in data.items():
                if k not in observed_keys:
                    observed_keys.add(k)
                    key_type_counts[k] = {"integer": 0, "float": 0, "string": 0, "boolean": 0, "null": 0, "object": 0, "list": 0}

                if v is None:
                    empty_value_count += 1
                    key_type_counts[k]["null"] += 1
                elif isinstance(v, bool):
                    key_type_counts[k]["boolean"] += 1
                elif isinstance(v, int):
                    key_type_counts[k]["integer"] += 1
                elif isinstance(v, float):
                    key_type_counts[k]["float"] += 1
                elif isinstance(v, str):
                    key_type_counts[k]["string"] += 1
                elif isinstance(v, dict):
                    key_type_counts[k]["object"] += 1
                elif isinstance(v, list):
                    key_type_counts[k]["list"] += 1

        except json.JSONDecodeError as e:
            malformed_count += 1
            if len(errors) < max_errors_retained:
                errors.append(ParseErrorDetail(
                    line_number=line_num,
                    error_type="JSON_DECODE_ERROR",
                    message=f"JSON syntax error on line {line_num}: {e}"
                ))

    sorted_keys = sorted(list(observed_keys))
    column_stats: List[ColumnStats] = []
    schema_parts: List[str] = []

    for k in sorted_keys:
        types = key_type_counts[k]
        null_count = types.get("null", 0)
        dominant_type = max((t for t in types if t != "null"), key=lambda x: types[x], default="string")
        column_stats.append(ColumnStats(
            name=k,
            inferred_type=dominant_type,
            null_or_empty_count=null_count
        ))
        schema_parts.append(f"{k}:{dominant_type}")

    schema_fingerprint = hashlib.sha256(",".join(schema_parts).encode("utf-8")).hexdigest()

    status = VerificationStatus.PASS
    if malformed_count > 0:
        status = VerificationStatus.WARNING if malformed_count < (record_count * 0.05) else VerificationStatus.FAIL
    elif record_count == 0:
        status = VerificationStatus.INCONCLUSIVE

    return ParsingResult(
        status=status,
        format=ExportFormat.JSONL,
        header=sorted_keys,
        column_count=len(sorted_keys),
        record_count=record_count,
        malformed_record_count=malformed_count,
        empty_value_count=empty_value_count,
        schema_fingerprint=schema_fingerprint,
        column_stats=column_stats,
        errors=errors,
        total_errors_count=malformed_count,
        bytes_consumed=raw_reader.total_bytes_read
    )

