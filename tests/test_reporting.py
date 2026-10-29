"""Tests for Module 12: Report Serialization (JSON, CSV, PDF)."""

import json
from pathlib import Path
import pytest

from dbguard.analyzer import analyze_export
from dbguard.reporting.csv_report import generate_csv_report
from dbguard.reporting.json_report import generate_json_report
from dbguard.reporting.pdf_report import generate_pdf_report


def test_report_serialization(tmp_path: Path):
    """Test 33: AnalysisReport serializes cleanly to JSON, CSV, and PDF without schema errors."""
    sample_gz = Path("sample_data/demo_e_matching_25k.csv.gz").resolve()
    manifest_file = Path("manifests/demo_e_matching_25k.manifest.json").resolve()

    report = analyze_export(sample_gz, manifest_path_or_dict=manifest_file)

    # 1. JSON
    json_path = tmp_path / "report.json"
    json_str = generate_json_report(report, json_path)
    assert json_path.exists()
    loaded = json.loads(json_str)
    assert loaded["report_id"] == report.report_id
    assert loaded["parsing_result"]["record_count"] == 25_000

    # 2. CSV
    csv_path = tmp_path / "report.csv"
    csv_str = generate_csv_report(report, csv_path)
    assert csv_path.exists()
    assert "DBGuard Analysis Summary Report" in csv_str
    assert "25000" in csv_str

    # 3. PDF
    pdf_path = tmp_path / "report.pdf"
    res_pdf = generate_pdf_report(report, pdf_path)
    assert res_pdf.exists()
    assert res_pdf.stat().st_size > 1000

