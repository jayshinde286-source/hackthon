"""Pydantic API response models."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    version: str
    system_time_utc: str
    features: List[str]


class FormatsResponse(BaseModel):
    compression_formats: List[str]
    export_formats: List[str]
    max_compressed_upload_mb: int
    default_chunk_size_kb: int


class IntegrityCheckItem(BaseModel):
    category: str
    check_name: str
    status: str
    observed_value: Optional[str] = None
    expected_value: Optional[str] = None
    explanation: Optional[str] = None
    evidence_reference: Optional[str] = None


class AnomalyItem(BaseModel):
    rule_id: str
    severity: str
    metric_name: str
    observed_value: Optional[str] = None
    expected_value: Optional[str] = None
    explanation: str
    recommendation: str


class RecoveryAssessmentItem(BaseModel):
    classification: str
    summary: str
    verified_properties: List[str]
    unverified_or_inconclusive: List[str]
    failures: List[str]
    recoverable_record_estimate: int
    recommended_actions: List[str]
    evidence_needed_for_full_claim: List[str]


class AnalysisSummary(BaseModel):
    id: str
    original_filename: str
    file_size_bytes: int
    compressed_size_bytes: int
    decompressed_size_bytes: int
    row_count: int
    column_count: int
    compression_format: str
    data_format: str
    compressed_sha256: str
    decompressed_sha256: Optional[str] = None
    schema_fingerprint: Optional[str] = None
    analysis_status: str
    recovery_assessment: str
    recovery_summary: str
    execution_duration_sec: float
    created_at: str


class AnalysisDetail(BaseModel):
    summary: AnalysisSummary
    checks: List[IntegrityCheckItem]
    anomalies: List[AnomalyItem]
    recovery: RecoveryAssessmentItem
    full_report: Dict[str, Any]


class ComparisonSummary(BaseModel):
    id: str
    previous_filename: str
    current_filename: str
    row_count_change_pct: Optional[float] = None
    compressed_size_change_pct: Optional[float] = None
    decompressed_size_change_pct: Optional[float] = None
    compression_ratio_old: float
    compression_ratio_new: float
    bytes_per_row_old: float
    bytes_per_row_new: float
    schema_match: bool
    summary_verdict: str
    created_at: str
    diffs: List[Dict[str, Any]]
    anomaly_flags: List[str]


class BenchmarkItem(BaseModel):
    experiment: str
    scenario: str
    rows: int
    compressed_bytes: int
    decompressed_bytes: int
    duration_sec: float
    peak_memory_mb: float
    throughput_rec_s: float
    created_at: str

