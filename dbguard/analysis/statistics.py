"""Module 9: Statistical utilities and safe metrics calculations."""

import math
from typing import List, Optional, Tuple


def safe_percentage_change(old_val: float, new_val: float) -> Optional[float]:
    """Calculate percentage change ((new - old) / old) * 100 safely."""
    if old_val == 0:
        return None
    return round(((new_val - old_val) / abs(old_val)) * 100.0, 2)


def calculate_compression_ratio(uncompressed_bytes: int, compressed_bytes: int) -> float:
    """Calculate compression ratio = uncompressed / compressed.

    A ratio > 1.0 indicates that data compressed to a smaller footprint.
    """
    if compressed_bytes <= 0:
        return 0.0
    return round(uncompressed_bytes / compressed_bytes, 4)


def calculate_bytes_per_row(decompressed_bytes: int, row_count: int) -> float:
    """Average uncompressed payload bytes per data row."""
    if row_count <= 0:
        return 0.0
    return round(decompressed_bytes / row_count, 2)


def calculate_median(values: List[float]) -> float:
    """Compute standard median."""
    if not values:
        return 0.0
    s = sorted(values)
    n = len(s)
    mid = n // 2
    if n % 2 == 1:
        return s[mid]
    return (s[mid - 1] + s[mid]) / 2.0


def calculate_mad(values: List[float], median: Optional[float] = None) -> float:
    """Compute Median Absolute Deviation (MAD), a robust outlier scale estimator."""
    if not values:
        return 0.0
    med = median if median is not None else calculate_median(values)
    deviations = [abs(x - med) for x in values]
    return calculate_median(deviations)


def calculate_iqr(values: List[float]) -> Tuple[float, float, float]:
    """Calculate Q1 (25th percentile), Q3 (75th percentile), and Interquartile Range (IQR)."""
    if not values:
        return 0.0, 0.0, 0.0
    s = sorted(values)
    n = len(s)
    q1 = s[int(n * 0.25)]
    q3 = s[int(n * 0.75)]
    return q1, q3, (q3 - q1)

