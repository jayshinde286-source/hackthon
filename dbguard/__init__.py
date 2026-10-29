"""DBGuard — Compressed Database Export Integrity Analyzer.

A streaming-based system for integrity verification, anomaly detection,
and recovery assessment of large compressed database exports without full database restoration.
"""

__version__ = "1.0.0"
__author__ = "DBGuard Research Team"

from dbguard.analyzer import analyze_export
from dbguard.models import (
    AnalysisReport,
    CompressionFormat,
    ExportFormat,
    ManifestProvenance,
    RecoveryClassification,
    VerificationStatus,
)

__all__ = [
    "analyze_export",
    "AnalysisReport",
    "VerificationStatus",
    "RecoveryClassification",
    "ManifestProvenance",
    "CompressionFormat",
    "ExportFormat",
]

