"""DBGuard Analysis Package."""

from dbguard.analysis.statistics import (
    calculate_compression_ratio,
    calculate_bytes_per_row,
    safe_percentage_change,
    calculate_median,
    calculate_mad,
    calculate_iqr,
)
from dbguard.analysis.comparison import compare_exports
from dbguard.analysis.anomalies import detect_anomalies
from dbguard.analysis.recovery_assessment import assess_recovery_feasibility

__all__ = [
    "calculate_compression_ratio",
    "calculate_bytes_per_row",
    "safe_percentage_change",
    "calculate_median",
    "calculate_mad",
    "calculate_iqr",
    "compare_exports",
    "detect_anomalies",
    "assess_recovery_feasibility",
]

