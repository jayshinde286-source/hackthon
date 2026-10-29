# DBGuard Algorithmic Specifications & Complexity Analysis

This document details the pseudocode, input/output definitions, and formal asymptotic complexity for the core algorithms implemented in DBGuard.

---

## Algorithm A: Unified Single-Pass Streaming Export Analysis

### Purpose
Processes a compressed database export file in a single bounded-memory pass to extract physical, cryptographic, and structural evidence without loading the uncompressed payload into RAM or writing decompressed files to disk.

### Pseudocode
```
Input: FilePath F, Config C, Optional Manifest M, Optional Baseline B
Output: Comprehensive AnalysisReport R

1.  Inspect file header magic bytes of F.
2.  If header is empty or unknown format:
        return INCONCLUSIVE or UNSUPPORTED_FORMAT report.
3.  Compute SHA-256 over compressed bytes in chunk size B (default 64 KB).
4.  Initialize Decompressor D, StreamHasher H_stream, ChunkHasher H_chunk (boundary K = 1MB).
5.  Initialize FormatParser P (CSV, JSONL, or SQL).
6.  Create StreamTapper generator:
        For each decompressed chunk c from D:
            Update H_stream with c
            Update H_chunk with c
            Track DecompressedBytes += len(c)
            If DecompressedBytes > C.max_decompressed_bytes:
                Raise ResourceLimitExceededError
            Yield c to P
7.  P consumes chunks incrementally:
        For each record r:
            Validate column count == header column count
            Update column type inferences and null counts
            Update RecordCount
8.  Finalize H_chunk to produce chunk list L_chunks.
9.  Construct MerkleTree T over L_chunks leaf hashes.
10. Calculate CompressionRatio = DecompressedBytes / CompressedBytes.
11. If Manifest M provided:
        Result_manifest = VerifyManifest(M, ObservedMetrics)
12. If Baseline B provided:
        Result_comparison = CompareExports(B, ObservedMetrics)
13. Execute AnomalyDetection(ObservedMetrics, M, B) -> AnomaliesList
14. Execute RecoveryAssessment(D_status, P_status, M_status, AnomaliesList) -> Verdict
15. Return AnalysisReport R
```

### Complexity Analysis
- **Time Complexity:** $O(N)$ where $N$ is the total decompressed byte length. Every byte is touched a constant number of times across decompressor, hasher, and parser.
- **Space Complexity:** $O(B + K)$ where $B$ is the streaming buffer size ($64\text{ KB}$) and $K$ is the chunk boundary buffer ($1\text{ MB}$). Peak heap memory is strictly decoupled from dataset size $N$.

---

## Algorithm B: Trusted Manifest Verification

### Purpose
Performs strict, field-by-field verification of observed export metrics against a cryptographic manifest, enforcing provenance boundaries.

### Pseudocode
```
Input: Manifest M, ObservedMetrics O, Optional SecretKey K
Output: ManifestVerificationResult

1.  Validate schema of M against DBGuard Version 1.0 schema.
2.  Evaluate Provenance P from M.trusted_reference_status:
        If P == OBSERVATIONAL_POST_HOC:
            Attach prominent warning: completeness not verified.
3.  If SecretKey K provided:
        Verify HMAC-SHA256 signature of M.
4.  Check: O.record_count == M.expected_row_count
5.  Check: O.decompressed_sha256 == M.uncompressed_sha256
6.  Check: O.schema_fingerprint == M.schema_fingerprint
7.  Check: O.chunk_hashes == M.chunk_hashes
8.  If any check fails:
        Assign overall_status = FAIL
    Else if any check missing:
        Assign overall_status = INCONCLUSIVE
    Else:
        Assign overall_status = PASS
9.  Return ManifestVerificationResult
```

### Complexity Analysis
- **Time Complexity:** $O(C)$ where $C$ is the number of chunk hashes in the manifest.
- **Space Complexity:** $O(C)$ to store the chunk metadata dictionary.

---

## Algorithm C: Explainable Rule-Based Anomaly Detection

### Purpose
Applies 14 deterministic rules and Median Absolute Deviation (MAD) historical statistics to detect physical, structural, and logical anomalies while preventing false corruption claims.

### Key Rules
1. `RULE_SIZE_DROP_ROW_INCREASE`: Flags when row count grows ($\ge +5\%$) while compressed file size shrinks ($\le -5\%$). Explains dictionary and repetition dynamics.
2. `RULE_UNCOMP_SIZE_DECREASE`: Flags when uncompressed size shrinks despite row count increasing.
3. `RULE_PARSE_ERRORS`: Detects malformed record rows with line numbers.
4. `RULE_MANIFEST_ROW_MISMATCH`: Flags discrepancy between manifest expected rows and observed rows.
5. `RULE_HISTORICAL_BPR_OUTLIER`: Flags when current Bytes Per Row deviates from historical median by $> 3.0 \times \text{MAD}$.

$$\text{MAD} = \text{median}(|X_i - \text{median}(X)|)$$

---

## Algorithm D: Chunk-Based Integrity & Merkle Tree Verification

### Purpose
Partitions the stream into fixed $1\text{ MB}$ slices to provide localized verification and cryptographic proof paths.

### Pseudocode
```
Leaf Construction:
    Hash_leaf(chunk) = SHA-256(0x00 || chunk)

Internal Node Construction:
    Hash_internal(left, right) = SHA-256(0x01 || left || right)

Odd Node Handling:
    If node count is odd, promote unpaired rightmost node directly to next layer.
```

---

## Algorithm E: Recovery Feasibility Assessment

### Purpose
Maps aggregated evidence to one of six standardized recovery classifications:

1. `VERIFIED_WITHIN_SCOPE`: Physical container valid, parser clean, and trusted pipeline manifest matches.
2. `LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED`: Physical container valid, parser clean, but manifest is missing or observational.
3. `RECOVERY_POSSIBLE_WITH_ERRORS`: Physical stream readable, but parsing detected malformed rows. Recoverable records estimated.
4. `INTEGRITY_FAILURE`: Physical stream truncated, CRC corrupted, or trusted manifest hash mismatch.
5. `INCONCLUSIVE`: Empty export or zero records parsed.
6. `UNSUPPORTED_FORMAT`: Unrecognized format header.

