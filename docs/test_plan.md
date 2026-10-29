# DBGuard Verification & Test Plan

## 1. Test Objectives
The automated test suite verifies:
1. Physical stream integrity across compression algorithms (Gzip, Bzip2, XZ, Zstandard).
2. Detection of truncated, corrupted, and empty files.
3. Accurate incremental parsing of CSV and SQL dump formats without full-memory buffering.
4. Correctness of cryptographic SHA-256 stream and chunk hashing, and Merkle tree proofs.
5. Strict manifest validation and provenance classification.
6. Anomaly detection accuracy, specifically the central problem statement condition (+30% rows, -20% size).
7. Resource exhaustion guards and security boundaries.

---

## 2. Test Execution Matrix (35 Automated Unit & Integration Tests)

| # | Test Identifier | Module Under Test | Condition Evaluated | Actual Result |
|---|---|---|---|---|
| 1 | `test_valid_gzip` | `compression.integrity` | Clean decompressed stream with valid CRC-32 trailer | **PASS** |
| 2 | `test_invalid_gzip_header` | `file_inspector` | Rejection of non-gzip header signature | **PASS** |
| 3 | `test_truncated_gzip` | `compression.integrity` | Truncation before trailer caught (`is_truncated=True`) | **PASS** |
| 4 | `test_corrupted_payload` | `compression.integrity` | Mutated byte in DEFLATE stream detected | **PASS** |
| 5 | `test_empty_file` | `file_inspector` | 0-byte file handled safely | **PASS** |
| 6 | `test_valid_empty_compressed_stream` | `compression.integrity` | Valid gzip header containing 0 uncompressed bytes | **PASS** |
| 7 | `test_valid_csv_with_header` | `parsers.csv_parser` | Column count, header, and record count verification | **PASS** |
| 8 | `test_csv_quoted_commas` | `parsers.csv_parser` | Commas inside quoted strings do not split columns | **PASS** |
| 9 | `test_csv_embedded_newlines` | `parsers.csv_parser` | Newlines inside quoted strings do not split records | **PASS** |
| 10 | `test_csv_inconsistent_columns` | `parsers.csv_parser` | Unequal column counts recorded as malformed records | **PASS** |
| 11 | `test_csv_empty_fields` | `parsers.csv_parser` | Null-like strings (`NULL`, `\N`, `""`) tracked | **PASS** |
| 12 | `test_unsupported_format` | `file_inspector` | Arbitrary binary rejected with `UNSUPPORTED_FORMAT` | **PASS** |
| 13 | `test_compressed_file_hash` | `hashing.file_hash` | Chunked SHA-256 matches exact whole-file hash | **PASS** |
| 14 | `test_decompressed_stream_hash` | `hashing.stream_hash` | Incremental stream SHA-256 matches decompressed bytes | **PASS** |
| 15 | `test_chunk_hashes` | `hashing.chunk_hash` | Exact 1MB boundary chunk digests | **PASS** |
| 16 | `test_matching_trusted_manifest` | `manifest.verifier` | Matching pipeline manifest yields PASS | **PASS** |
| 17 | `test_incorrect_manifest_hash` | `manifest.verifier` | Mismatched uncompressed hash yields FAIL | **PASS** |
| 18 | `test_incorrect_expected_row_count` | `manifest.verifier` | Discrepant expected row count yields FAIL | **PASS** |
| 19 | `test_missing_manifest_fields` | `manifest.schema` | Missing required fields rejected by schema validator | **PASS** |
| 20 | `test_unsupported_manifest_version` | `manifest.schema` | Version != 1.0 raises ManifestError | **PASS** |
| 21 | `test_untrusted_manifest_provenance`| `manifest.trust` | Post-hoc manifest flagged with provenance warning | **PASS** |
| 22 | `test_identical_exports_comparison` | `analysis.comparison` | Identical export diff yields 0% change | **PASS** |
| 23 | `test_different_exports_same_row_count`| `analysis.comparison`| Metric diffs calculated when row count is identical | **PASS** |
| 24 | `test_larger_export_smaller_compressed_size`| `analysis.anomalies` | **The Core Problem Statement:** +30% rows / -20% size flagged as WARNING without false corruption claim | **PASS** |
| 25 | `test_schema_mismatch_detection` | `analysis.anomalies` | Changed columns detected in schema diff | **PASS** |
| 26 | `test_statistical_anomaly_insufficient_history`| `analysis.anomalies`| < 5 historical observations reports limited confidence | **PASS** |
| 27 | `test_merkle_tree_proofs_and_odd_nodes`| `hashing.merkle` | Odd node promotion and audit path proof verification | **PASS** |
| 28 | `test_streaming_bounded_memory` | `parsers.csv_parser` | Consumes 5,000 chunks without buffer accumulation | **PASS** |
| 29 | `test_decompression_size_limit` | `compression.streaming`| Decompression aborts on exceeding max byte ceiling | **PASS** |
| 30 | `test_expansion_ratio_protection` | `compression.streaming`| Zip bomb expansion ceiling (> 100x) stops decompression | **PASS** |
| 31 | `test_unsafe_path_handling` | `utils.safe_paths` | Null byte injection blocked with SecurityError | **PASS** |
| 32 | `test_original_file_unmodified` | `analyzer` | Original file bytes and mtime timestamp remain identical | **PASS** |
| 33 | `test_report_serialization` | `reporting` | Clean export to PDF, JSON, and CSV | **PASS** |
| 34 | `test_recovery_assessment_classifications`| `analysis.recovery_assessment`| Strict mapping to all 6 recovery categories | **PASS** |
| 35 | `test_sql_parser_behavior` | `parsers.sql_parser` | Multiline / multi-row INSERTs and PostgreSQL COPY | **PASS** |

---

## 3. Test Execution Command
```bash
source .venv/bin/activate
pytest -v
# Result: 35 passed in 0.23s
```

