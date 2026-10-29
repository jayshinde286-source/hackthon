"""DBGuard Core Data Models and Enums.

Defines typed, immutable or structured dataclasses and standardized enums for all
stages of the integrity verification, anomaly detection, and recovery assessment pipeline.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any, Optional, Dict, List


class VerificationStatus(str, Enum):
    """Standardized result categories for individual checks and overall results."""
    PASS = "PASS"
    FAIL = "FAIL"
    WARNING = "WARNING"
    INCONCLUSIVE = "INCONCLUSIVE"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class RecoveryClassification(str, Enum):
    """Assessment of export usability for data recovery."""
    VERIFIED_WITHIN_SCOPE = "VERIFIED_WITHIN_SCOPE"
    LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED = "LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED"
    RECOVERY_POSSIBLE_WITH_ERRORS = "RECOVERY_POSSIBLE_WITH_ERRORS"
    INTEGRITY_FAILURE = "INTEGRITY_FAILURE"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNSUPPORTED_FORMAT = "UNSUPPORTED_FORMAT"


class ManifestProvenance(str, Enum):
    """Origin and trustworthiness of an integrity manifest."""
    TRUSTED_EXPORT_PIPELINE = "TRUSTED_EXPORT_PIPELINE"
    INDEPENDENT_SOURCE = "INDEPENDENT_SOURCE"
    OBSERVATIONAL_POST_HOC = "OBSERVATIONAL_POST_HOC"
    UNKNOWN = "UNKNOWN"


class CompressionFormat(str, Enum):
    """Supported compression stream formats."""
    GZIP = "gzip"
    BZIP2 = "bzip2"
    XZ = "xz"
    ZSTD = "zstandard"
    UNCOMPRESSED = "uncompressed"
    UNKNOWN = "unknown"


class ExportFormat(str, Enum):
    """Supported structured export data formats."""
    CSV = "csv"
    JSONL = "jsonl"
    SQL_DUMP = "sql_dump"
    UNKNOWN = "unknown"


class AnomalySeverity(str, Enum):
    """Severity ratings for detected anomalies."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    WARNING = "WARNING"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class FileInspection:
    """Intake inspection metadata for the input file."""
    path: str
    filename: str
    file_size_bytes: int
    detected_compression: CompressionFormat
    sha256_compressed: str
    is_empty: bool
    is_valid_header: bool
    header_hex: str
    inspection_notes: List[str] = field(default_factory=list)


@dataclass
class CompressionValidationResult:
    """Format-specific physical stream validation results."""
    status: VerificationStatus
    format: CompressionFormat
    compressed_bytes_read: int
    decompressed_bytes: int
    expansion_ratio: float
    sha256_decompressed: str
    is_truncated: bool
    crc_or_trailer_valid: Optional[bool] = None
    error_message: Optional[str] = None
    limitations: List[str] = field(default_factory=list)


@dataclass
class ParseErrorDetail:
    """Record of a parsing anomaly or syntax violation."""
    line_number: int
    error_type: str
    message: str


@dataclass
class ColumnStats:
    """Statistical summary of a parsed table column."""
    name: str
    inferred_type: str
    null_or_empty_count: int
    sample_min: Optional[str] = None
    sample_max: Optional[str] = None


@dataclass
class ParsingResult:
    """Output from the streaming record parser."""
    status: VerificationStatus
    format: ExportFormat
    header: List[str]
    column_count: int
    record_count: int
    malformed_record_count: int
    empty_value_count: int
    schema_fingerprint: str
    column_stats: List[ColumnStats] = field(default_factory=list)
    errors: List[ParseErrorDetail] = field(default_factory=list)
    total_errors_count: int = 0
    bytes_consumed: int = 0


@dataclass
class ChunkHashEntry:
    """Hash for an individual chunk in a fixed-size chunking scheme."""
    index: int
    start_byte: int
    end_byte: int
    length_bytes: int
    sha256: str
    record_count: Optional[int] = None


@dataclass
class HashResult:
    """Cryptographic hashes across multiple granularities."""
    compressed_sha256: str
    decompressed_sha256: str
    chunk_hashes: List[ChunkHashEntry] = field(default_factory=list)
    merkle_root: Optional[str] = None
    canonical_record_hash: Optional[str] = None


@dataclass
class ManifestCheckDetail:
    """Verification result for a single manifest field."""
    field_name: str
    status: VerificationStatus
    expected: Any
    observed: Any
    message: str


@dataclass
class ManifestVerificationResult:
    """Comprehensive evaluation of export against a trusted manifest."""
    overall_status: VerificationStatus
    manifest_provenance: ManifestProvenance
    checks: List[ManifestCheckDetail] = field(default_factory=list)
    provenance_warning: Optional[str] = None
    limitations: List[str] = field(default_factory=list)


@dataclass
class ExportMetrics:
    """Normalized metrics summarizing an export file for comparison and tracking."""
    compressed_size_bytes: int
    decompressed_size_bytes: int
    row_count: int
    compression_ratio: float  # uncompressed / compressed
    bytes_per_row: float
    schema_fingerprint: str
    column_count: int
    malformed_count: int


@dataclass
class MetricDiff:
    """Comparison diff between an old and new export metric."""
    metric_name: str
    old_value: Any
    new_value: Any
    absolute_change: float
    percentage_change: Optional[float] = None


@dataclass
class ExportComparison:
    """Detailed comparison between an earlier export and a newer export."""
    old_metrics: ExportMetrics
    new_metrics: ExportMetrics
    diffs: List[MetricDiff]
    schema_match: bool
    added_columns: List[str]
    removed_columns: List[str]
    summary_verdict: str
    anomaly_flags: List[str] = field(default_factory=list)


@dataclass
class Anomaly:
    """Explainable anomaly detection flag with evidence and recommendations."""
    rule_id: str
    severity: AnomalySeverity
    metric_name: str
    observed_value: Any
    expected_or_baseline: Any
    threshold: Any
    explanation: str
    recommendation: str
    evidence_ref: str
    confidence_limitations: str


@dataclass
class RecoveryAssessment:
    """Evaluation of data recovery usability and limitations."""
    classification: RecoveryClassification
    summary: str
    verified_properties: List[str]
    unverified_or_inconclusive: List[str]
    failures: List[str]
    recoverable_record_estimate: int
    recommended_actions: List[str]
    evidence_needed_for_full_claim: List[str]


@dataclass
class AnalysisReport:
    """Complete, serializable analysis report for DBGuard."""
    report_id: str
    tool_name: str
    tool_version: str
    generated_at_utc: str
    file_inspection: FileInspection
    compression_validation: CompressionValidationResult
    parsing_result: ParsingResult
    hash_result: HashResult
    manifest_verification: Optional[ManifestVerificationResult]
    anomalies: List[Anomaly]
    recovery_assessment: RecoveryAssessment
    execution_duration_sec: float
    config_snapshot: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire report into a clean, serializable dict."""
        return asdict(self)
