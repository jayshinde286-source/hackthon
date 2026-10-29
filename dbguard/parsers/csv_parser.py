"""Module 4: Streaming CSV Parser.

Performs robust, bounded-memory CSV parsing directly over decompressed byte streams.
Correctly handles quoted fields with embedded commas and newlines without naive line splitting.
Tracks column structure, null counts, type inferences, malformed records, and computes a schema fingerprint.
"""

import csv
import hashlib
import io
import re
from typing import Iterator, List, Optional, Dict

from dbguard.parsers.stream_adapter import ChunkGeneratorReader
from dbguard.models import (
    ColumnStats,
    ExportFormat,
    ParseErrorDetail,
    ParsingResult,
    VerificationStatus,
)

ISO_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}(?:[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:?\d{2})?$")
NULL_REPRESENTATIONS = {"", "null", "none", "\\n", "nan", "nil"}


def _infer_type(value: str) -> str:
    """Infer basic data type of a string representation."""
    val_strip = value.strip()
    if not val_strip or val_strip.lower() in NULL_REPRESENTATIONS:
        return "unknown"
    if val_strip.isdigit() or (val_strip.startswith("-") and val_strip[1:].isdigit()):
        return "integer"
    try:
        float(val_strip)
        return "float"
    except ValueError:
        pass
    if ISO_DATE_PATTERN.match(val_strip):
        return "timestamp"
    if val_strip.lower() in ("true", "false", "t", "f"):
        return "boolean"
    return "string"


def parse_csv_stream(
    byte_chunks: Iterator[bytes],
    delimiter: str = ",",
    quotechar: str = '"',
    encoding: str = "utf-8",
    has_header: bool = True,
    max_field_size: int = 1_048_576,
    max_errors_retained: int = 100,
) -> ParsingResult:
    """Parse CSV records from an uncompressed byte chunk iterator in streaming fashion.

    Args:
        byte_chunks: Iterator yielding uncompressed bytes.
        delimiter: CSV field separator.
        quotechar: CSV quotation character.
        encoding: Character encoding.
        has_header: Whether the first row represents the column header.
        max_field_size: Maximum allowed length for a single CSV field.
        max_errors_retained: Maximum detailed parse errors kept in memory.

    Returns:
        ParsingResult with record counts, schema fingerprint, and diagnostics.
    """
    csv.field_size_limit(max_field_size)

    raw_reader = ChunkGeneratorReader(byte_chunks)
    text_stream = io.TextIOWrapper(
        io.BufferedReader(raw_reader, buffer_size=65_536),
        encoding=encoding,
        errors="replace",
        newline=""  # Required by standard csv module
    )

    csv_reader = csv.reader(text_stream, delimiter=delimiter, quotechar=quotechar)

    header: List[str] = []
    column_count = 0
    record_count = 0
    malformed_count = 0
    empty_value_count = 0
    errors: List[ParseErrorDetail] = []
    col_type_votes: List[Dict[str, int]] = []
    col_null_counts: List[int] = []
    col_min: List[Optional[str]] = []
    col_max: List[Optional[str]] = []

    line_num = 0

    try:
        for row in csv_reader:
            line_num += 1

            if line_num == 1 and has_header:
                header = [c.strip() for c in row]
                column_count = len(header)
                col_type_votes = [{"integer": 0, "float": 0, "timestamp": 0, "boolean": 0, "string": 0} for _ in range(column_count)]
                col_null_counts = [0] * column_count
                col_min = [None] * column_count
                col_max = [None] * column_count
                continue

            # Process data row
            record_count += 1

            # Validate column count consistency
            if column_count > 0 and len(row) != column_count:
                malformed_count += 1
                if len(errors) < max_errors_retained:
                    errors.append(ParseErrorDetail(
                        line_number=line_num,
                        error_type="COL_COUNT_MISMATCH",
                        message=f"Expected {column_count} columns, found {len(row)} at line {line_num}."
                    ))
                continue

            # If no header was present, initialize from first row
            if column_count == 0:
                column_count = len(row)
                header = [f"col_{i+1}" for i in range(column_count)]
                col_type_votes = [{"integer": 0, "float": 0, "timestamp": 0, "boolean": 0, "string": 0} for _ in range(column_count)]
                col_null_counts = [0] * column_count
                col_min = [None] * column_count
                col_max = [None] * column_count

            # Track column statistics and types
            for idx, cell in enumerate(row):
                cell_strip = cell.strip()
                if not cell_strip or cell_strip.lower() in NULL_REPRESENTATIONS:
                    empty_value_count += 1
                    col_null_counts[idx] += 1
                else:
                    inferred = _infer_type(cell_strip)
                    if inferred in col_type_votes[idx]:
                        col_type_votes[idx][inferred] += 1

                    # Track min/max
                    curr_min = col_min[idx]
                    curr_max = col_max[idx]
                    if curr_min is None or cell_strip < curr_min:
                        col_min[idx] = cell_strip[:64]
                    if curr_max is None or cell_strip > curr_max:
                        col_max[idx] = cell_strip[:64]

    except csv.Error as e:
        malformed_count += 1
        if len(errors) < max_errors_retained:
            errors.append(ParseErrorDetail(
                line_number=line_num + 1,
                error_type="CSV_PARSING_SYNTAX_ERROR",
                message=f"CSV parser syntax violation: {e}"
            ))

    # Resolve finalized column statistics and types
    column_stats: List[ColumnStats] = []
    schema_parts: List[str] = []

    for i in range(column_count):
        votes = col_type_votes[i]
        # Type with highest vote count, defaulting to string
        resolved_type = "string"
        max_votes = -1
        for t, count in votes.items():
            if count > max_votes and count > 0:
                max_votes = count
                resolved_type = t

        col_name = header[i] if i < len(header) else f"col_{i+1}"
        column_stats.append(ColumnStats(
            name=col_name,
            inferred_type=resolved_type,
            null_or_empty_count=col_null_counts[i],
            sample_min=col_min[i],
            sample_max=col_max[i]
        ))
        schema_parts.append(f"{col_name}:{resolved_type}")

    # Compute deterministic schema fingerprint (SHA-256 over canonical schema string)
    schema_str = ",".join(schema_parts)
    schema_fingerprint = hashlib.sha256(schema_str.encode("utf-8")).hexdigest()

    status = VerificationStatus.PASS
    if malformed_count > 0:
        status = VerificationStatus.WARNING if malformed_count < (record_count * 0.05) else VerificationStatus.FAIL
    elif record_count == 0 and not header:
        status = VerificationStatus.INCONCLUSIVE

    return ParsingResult(
        status=status,
        format=ExportFormat.CSV,
        header=header,
        column_count=column_count,
        record_count=record_count,
        malformed_record_count=malformed_count,
        empty_value_count=empty_value_count,
        schema_fingerprint=schema_fingerprint,
        column_stats=column_stats,
        errors=errors,
        total_errors_count=malformed_count,
        bytes_consumed=raw_reader.total_bytes_read
    )

