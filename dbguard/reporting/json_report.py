"""Module 12: JSON Report Serializer."""

import json
from pathlib import Path
from typing import Optional, Union
from dbguard.models import AnalysisReport
from dbguard.utils.safe_paths import safe_output_path


def generate_json_report(report: AnalysisReport, output_path: Optional[Union[str, Path]] = None) -> str:
    """Serialize AnalysisReport into a clean, formatted JSON string and optionally save to disk."""
    report_dict = report.to_dict()
    json_str = json.dumps(report_dict, indent=2)

    if output_path:
        p = safe_output_path(output_path, allow_overwrite=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write(json_str)

    return json_str
