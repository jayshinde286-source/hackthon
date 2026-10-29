"""Tests for Module 6: SQL Dump Parser."""

from dbguard.parsers.sql_parser import parse_sql_dump_stream
from dbguard.models import VerificationStatus, ExportFormat


def _to_chunks(text: str, chunk_size: int = 32):
    data = text.encode("utf-8")
    for i in range(0, len(data), chunk_size):
        yield data[i:i + chunk_size]


def test_sql_parser_behavior():
    """Test 35: SQL parser handles multi-row multiline INSERTs and ignores semicolons in string literals."""
    sql_text = """
    -- Database Export Dump
    CREATE TABLE users (id INT, name VARCHAR(100), note TEXT);

    INSERT INTO users VALUES (1, 'Alice', 'First note; has semicolon'), (2, 'Bob', 'Second note');

    /* Multiline insert */
    INSERT INTO users
    VALUES
        (3, 'Charlie', 'Note with escaped \\' quote'),
        (4, 'David', 'Note with embedded (parenthesis) inside quotes');

    -- PostgreSQL COPY section
    COPY orders (order_id, user_id, amount) FROM stdin;
    101\t1\t50.00
    102\t2\t75.50
    103\t3\t120.00
    \\.
    """
    res = parse_sql_dump_stream(_to_chunks(sql_text))

    assert res.status == VerificationStatus.PASS
    # 2 rows in first insert + 2 rows in second insert + 3 rows in COPY = 7 records
    assert res.record_count == 7
    assert "users" in res.header
    assert "orders" in res.header

