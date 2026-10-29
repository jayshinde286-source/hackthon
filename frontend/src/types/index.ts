export type VerificationStatus = 'PASS' | 'FAIL' | 'WARNING' | 'INCONCLUSIVE' | 'NOT_APPLICABLE';

export type RecoveryClassification =
  | 'VERIFIED_WITHIN_SCOPE'
  | 'LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED'
  | 'RECOVERY_POSSIBLE_WITH_ERRORS'
  | 'INTEGRITY_FAILURE'
  | 'INCONCLUSIVE'
  | 'UNSUPPORTED_FORMAT';

export interface IntegrityCheckItem {
  category: string;
  check_name: string;
  status: VerificationStatus;
  observed_value?: string;
  expected_value?: string;
  explanation?: string;
  evidence_reference?: string;
}

export interface AnomalyItem {
  rule_id: string;
  severity: 'CRITICAL' | 'HIGH' | 'WARNING' | 'MEDIUM' | 'LOW' | 'INFO';
  metric_name: string;
  observed_value?: string;
  expected_value?: string;
  explanation: string;
  recommendation: string;
}

export interface RecoveryAssessmentItem {
  classification: RecoveryClassification;
  summary: string;
  verified_properties: string[];
  unverified_or_inconclusive: string[];
  failures: string[];
  recoverable_record_estimate: number;
  recommended_actions: string[];
  evidence_needed_for_full_claim: string[];
}

export interface AnalysisSummary {
  id: string;
  original_filename: string;
  file_size_bytes: number;
  compressed_size_bytes: number;
  decompressed_size_bytes: number;
  row_count: number;
  column_count: number;
  compression_format: string;
  data_format: string;
  compressed_sha256: string;
  decompressed_sha256?: string;
  schema_fingerprint?: string;
  analysis_status: VerificationStatus;
  recovery_assessment: RecoveryClassification;
  recovery_summary: string;
  execution_duration_sec: number;
  created_at: string;
}

export interface AnalysisDetail {
  summary: AnalysisSummary;
  checks: IntegrityCheckItem[];
  anomalies: AnomalyItem[];
  recovery: RecoveryAssessmentItem;
  full_report: any;
}

export interface ComparisonDiff {
  metric: string;
  old: number;
  new: number;
  change_pct?: number;
}

export interface ComparisonSummary {
  id: string;
  previous_filename: string;
  current_filename: string;
  row_count_change_pct?: number;
  compressed_size_change_pct?: number;
  decompressed_size_change_pct?: number;
  compression_ratio_old: number;
  compression_ratio_new: number;
  bytes_per_row_old: number;
  bytes_per_row_new: number;
  schema_match: boolean;
  summary_verdict: string;
  created_at: string;
  diffs: ComparisonDiff[];
  anomaly_flags: string[];
}

export interface BenchmarkItem {
  experiment: string;
  scenario: string;
  rows: number;
  compressed_bytes: number;
  decompressed_bytes: number;
  duration_sec: number;
  peak_memory_mb: number;
  throughput_rec_s: number;
  created_at: string;
}

export interface DemoScenario {
  id: string;
  title: string;
  description: string;
  file: string;
  has_manifest: boolean;
}

