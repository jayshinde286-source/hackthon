"""Tests for Module 4: Streaming CSV Parser."""

import io
import pytest
from dbguard.parsers.csv_parser import parse_csv_stream
from dbguard.models import VerificationStatus, ExportFormat


def _to_chunks(text: str, chunk_size: int = 16):
    """Helper to simulate incremental byte chunks from a decompressor."""
    data = text.encode("utf-8")
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def test_valid_csv_with_header():
    """Test 7: Valid CSV with standard header and rows."""
    csv_text = "id,name,amount\n1,Alice,10.50\n2,Bob,20.00\n3,Charlie,30.25\n"
    res = parse_csv_stream(_to_chunks(csv_text))

    assert res.status == VerificationStatus.PASS
    assert res.record_count == 3
    assert res.column_count == 3
    assert res.header == ["id", "name", "amount"]
    assert res.malformed_record_count == 0


def test_csv_quoted_commas():
    """Test 8: CSV with quoted fields containing commas."""
    csv_text = 'id,address,city\n1,"Suite 100, Building B, North Tower",Seattle\n2,"123 Main St, Apt 4",Portland\n'
    res = parse_csv_stream(_to_chunks(csv_text))

    assert res.status == VerificationStatus.PASS
    assert res.record_count == 2
    assert res.column_count == 3
    assert res.malformed_record_count == 0


def test_csv_embedded_newlines():
    """Test 9: CSV with quoted fields containing embedded newlines."""
    csv_text = 'id,comment,author\n1,"Line 1 of comment\nLine 2 of comment\nLine 3 of comment",Alice\n2,"Single line",Bob\n'
    res = parse_csv_stream(_to_chunks(csv_text))

    # Crucial test: embedded newlines must NOT increment row count
    assert res.status == VerificationStatus.PASS
    assert res.record_count == 2
    assert res.column_count == 3
    assert res.malformed_record_count == 0


def test_csv_inconsistent_columns():
    """Test 10: Inconsistent column counts are recorded as malformed records."""
    csv_text = (
        "id,colA,colB\n"
        "1,valA,valB\n"
        "2,valA,valB,EXTRA_VALUE\n"  # 4 cols instead of 3
        "3,valA\n"                   # 2 cols instead of 3
        "4,valA,valB\n"
    )
    res = parse_csv_stream(_to_chunks(csv_text))

    assert res.malformed_record_count == 2
    assert res.record_count == 4
    assert len(res.errors) == 2


def test_csv_empty_fields():
    """Test 11: CSV containing null and empty representations."""
    csv_text = "id,val1,val2,val3\n1,,NULL,foo\n2,\\N,bar,\n3,None,baz,100\n"
    res = parse_csv_stream(_to_chunks(csv_text))

    assert res.record_count == 3
    assert res.empty_value_count == 5


def test_streaming_bounded_memory():
    """Test 28: Streaming parser consumes large sequence of chunks without accumulating all lines in RAM."""
    def infinite_chunks(count=10_000):
        yield b"id,val\n"
        for i in range(1, count + 1):
            yield f"{i},value_{i}\n".encode("utf-8")

    res = parse_csv_stream(infinite_chunks(count=5_000))
    assert res.record_count == 5_000
    assert res.malformed_record_count == 0
