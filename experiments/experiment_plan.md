# DBGuard Empirical Experiment Plan

## 1. Experimental Objectives
The empirical evaluation aims to scientifically validate whether DBGuard can assess compressed database exports without full database restoration, while addressing the central problem statement:
> *"A 30% increase in row count coincided with a 20% decrease in compressed file size. Is this file corrupted?"*

We formulate three testable engineering hypotheses:
- **Hypothesis 1 (Bounded Memory Scalability):** DBGuard's single-pass streaming architecture maintains peak working memory bounded by buffer size $O(B)$ rather than dataset size $O(N)$, whereas full in-memory loading grows linearly with $N$.
- **Hypothesis 2 (Entropy Decoupling):** Compression ratio and compressed file size are functions of data entropy and repetition, not monotonic row count. Legitimate exports can be smaller despite having more records.
- **Hypothesis 3 (Evidence Separation):** Physical container integrity (CRC/trailer) is decoupled from logical completeness. A stream can pass decompression while missing 15% of records, detectable only via independent pipeline manifests.

---

## 2. Experimental Protocols

### Experiment 1: Large-File Scalability
- **Variables:** Record count $N \in \{10000, 50000, 100000, 250000\}$.
- **Metrics:** Compressed bytes, decompressed bytes, execution duration (seconds), peak memory (MB via `tracemalloc`), throughput (MB/s and records/s).
- **Target:** Verify that peak memory remains sub-megabyte across scaling factors.

### Experiment 2: Compression Variability & The Core Anomaly
- **Variables:** Record count (100k vs 130k rows) and repetition mode (normal entropy vs repetitive categorical data).
- **Metrics:** Compression ratio ($uncompressed / compressed$), bytes per record, compressed size.
- **Target:** Reproduce the exact scenario where a 130k row file is smaller than a 100k row file.

### Experiment 3: Streaming vs Full-Memory Loading
- **Variables:** Streaming pipeline vs in-memory loading (`read()` + `splitlines()`).
- **Metrics:** Peak allocated heap memory and execution duration.
- **Target:** Quantify RAM reduction percentage achieved by DBGuard.

### Experiment 4: Cryptographic Chunk & Merkle Tree Verification
- **Variables:** Fixed 1MB chunk hashes vs full-stream hashes.
- **Metrics:** Number of chunks, localized mismatch detection, Merkle root verification.

---

## 3. Data Output
All measured timings, bytes, and memory metrics will be recorded in:
- `experiments/benchmark_results.csv`
- `experiments/results_analysis.md`

