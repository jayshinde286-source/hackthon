"""Module 6: Streaming SQL Dump Parser.

Provides an explicitly scoped tokenizer and state machine for standard SQL dumps:
- MySQL/Standard SQL INSERT INTO table VALUES (...), (...); statements (including multiline and multi-row).
- PostgreSQL COPY ... FROM stdin; data streams.
- Distinguishes DDL from DML without executing SQL or connecting to any database.
- Ignores semicolons inside quoted literals and comments.
"""

import hashlib
import io
import re
from typing import Iterator, List, Optional, Tuple

from dbguard.parsers.stream_adapter import ChunkGeneratorReader
from dbguard.models import (
    ColumnStats,
    ExportFormat,
    ParseErrorDetail,
    ParsingResult,
    VerificationStatus,
)


def _count_tuples_in_values_clause(values_body: str) -> int:
    """Count top-level parenthesized record tuples: (a, b), (c, d) in a VALUES clause."""
    in_sq = False
    in_dq = False
    escape = False
    paren_depth = 0
    tuple_count = 0

    for ch in values_body:
        if escape:
            escape = False
            continue
        if ch == "\\":
            escape = True
            continue

        if ch == "'" and not in_dq:
            in_sq = not in_sq
            continue
        if ch == '"' and not in_sq:
            in_dq = not in_dq
            continue

        if not in_sq and not in_dq:
            if ch == "(":
                if paren_depth == 0:
                    tuple_count += 1
                paren_depth += 1
            elif ch == ")":
                if paren_depth > 0:
                    paren_depth -= 1

    return tuple_count


def parse_sql_dump_stream(
    byte_chunks: Iterator[bytes],
    encoding: str = "utf-8",
    max_errors_retained: int = 100,
) -> ParsingResult:
    """Parse supported SQL dump streams incrementally using a deterministic state machine.

    Args:
        byte_chunks: Stream of uncompressed bytes.
        encoding: Character encoding.
        max_errors_retained: Error retention bound.

    Returns:
        ParsingResult with counted data rows and schema statements.
    """
    raw_reader = ChunkGeneratorReader(byte_chunks)
    text_stream = io.TextIOWrapper(
        io.BufferedReader(raw_reader, buffer_size=65_536),
        encoding=encoding,
        errors="replace"
    )

    record_count = 0
    malformed_count = 0
    errors: List[ParseErrorDetail] = []
    tables_found: List[str] = []
    header: List[str] = []

    # State machine variables
    in_single_quote = False
    in_double_quote = False
    in_block_comment = False
    in_copy_mode = False
    copy_table_name = ""

    current_statement_tokens: List[str] = []
    line_num = 0

    for raw_line in text_stream:
        line_num += 1
        line = raw_line.strip()

        # Handle PostgreSQL COPY stdin data lines
        if in_copy_mode:
            if line == "\\.":
                in_copy_mode = False
            else:
                record_count += 1
            continue

        # Check line comments if not inside quotes
        if not in_single_quote and not in_double_quote and not in_block_comment:
            if line.startswith("--") or line.startswith("#"):
                continue

        # Parse character-by-character
        i = 0
        buf = []
        while i < len(raw_line):
            ch = raw_line[i]

            # Block comment start/end
            if not in_single_quote and not in_double_quote:
                if not in_block_comment and i + 1 < len(raw_line) and raw_line[i:i+2] == "/*":
                    in_block_comment = True
                    i += 2
                    continue
                elif in_block_comment and i + 1 < len(raw_line) and raw_line[i:i+2] == "*/":
                    in_block_comment = False
                    i += 2
                    continue

            if in_block_comment:
                i += 1
                continue

            # Escaping inside quotes
            if ch == "\\" and (in_single_quote or in_double_quote):
                buf.append(ch)
                if i + 1 < len(raw_line):
                    buf.append(raw_line[i+1])
                    i += 2
                else:
                    i += 1
                continue

            # Quote toggles
            if ch == "'" and not in_double_quote:
                in_single_quote = not in_single_quote
                buf.append(ch)
                i += 1
                continue
            elif ch == '"' and not in_single_quote:
                in_double_quote = not in_double_quote
                buf.append(ch)
                i += 1
                continue

            # Semicolon outside quotes finishes a statement
            if ch == ";" and not in_single_quote and not in_double_quote:
                stmt_str = "".join(buf).strip()
                buf = []
                full_stmt = (" ".join(current_statement_tokens) + " " + stmt_str).strip()
                current_statement_tokens = []

                if full_stmt:
                    # Classify statement
                    upper_stmt = full_stmt.upper()
                    if upper_stmt.startswith("INSERT INTO") or upper_stmt.startswith("INSERT IGNORE INTO") or upper_stmt.startswith("REPLACE INTO"):
                        # Extract table name
                        match_tbl = re.search(r"INSERT\s+(?:IGNORE\s+)?INTO\s+[`\"']?([a-zA-Z0-9_]+)[`\"']?", full_stmt, re.IGNORECASE)
                        if match_tbl:
                            tbl = match_tbl.group(1)
                            if tbl not in tables_found:
                                tables_found.append(tbl)

                        # Find VALUES clause
                        match_vals = re.search(r"\bVALUES\b\s*(.*)", full_stmt, re.IGNORECASE | re.DOTALL)
                        if match_vals:
                            vals_part = match_vals.group(1)
                            counted = _count_tuples_in_values_clause(vals_part)
                            if counted > 0:
                                record_count += counted
                            else:
                                malformed_count += 1
                                if len(errors) < max_errors_retained:
                                    errors.append(ParseErrorDetail(
                                        line_number=line_num,
                                        error_type="SQL_INSERT_ZERO_TUPLES",
                                        message=f"INSERT statement found but could not parse record tuples at line {line_num}."
                                    ))
                        else:
                            # Might be INSERT INTO ... SELECT
                            if len(errors) < max_errors_retained:
                                errors.append(ParseErrorDetail(
                                    line_number=line_num,
                                    error_type="UNSUPPORTED_INSERT_SYNTAX",
                                    message="INSERT ... SELECT or non-standard INSERT statement encountered."
                                ))
                    elif upper_stmt.startswith("COPY ") and "FROM STDIN" in upper_stmt:
                        match_copy = re.search(r"COPY\s+[`\"']?([a-zA-Z0-9_]+)[`\"']?", full_stmt, re.IGNORECASE)
                        if match_copy:
                            copy_table_name = match_copy.group(1)
                            if copy_table_name not in tables_found:
                                tables_found.append(copy_table_name)
                        in_copy_mode = True
                    elif upper_stmt.startswith("CREATE TABLE"):
                        match_create = re.search(r"CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?[`\"']?([a-zA-Z0-9_]+)[`\"']?", full_stmt, re.IGNORECASE)
                        if match_create:
                            tbl = match_create.group(1)
                            if tbl not in tables_found:
                                tables_found.append(tbl)

                i += 1
                continue

            buf.append(ch)
            i += 1

        rem = "".join(buf).strip()
        if rem:
            current_statement_tokens.append(rem)

    header = tables_found if tables_found else ["sql_data"]
    schema_fingerprint = hashlib.sha256(",".join(tables_found).encode("utf-8")).hexdigest()

    status = VerificationStatus.PASS
    if record_count == 0 and not tables_found:
        status = VerificationStatus.INCONCLUSIVE
    elif malformed_count > 0:
        status = VerificationStatus.WARNING

    return ParsingResult(
        status=status,
        format=ExportFormat.SQL_DUMP,
        header=header,
        column_count=len(header),
        record_count=record_count,
        malformed_record_count=malformed_count,
        empty_value_count=0,
        schema_fingerprint=schema_fingerprint,
        column_stats=[ColumnStats(name=t, inferred_type="sql_table", null_or_empty_count=0) for t in tables_found],
        errors=errors,
        total_errors_count=malformed_count,
        bytes_consumed=raw_reader.total_bytes_read
    )

