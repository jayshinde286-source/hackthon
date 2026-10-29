# DBGuard User Manual & Operations Guide

## 1. Quick Start & Setup

### Environment Activation
Ensure Python 3.11+ is installed. Activate the project virtual environment:
```bash
source .venv/bin/activate
python scripts/verify_environment.py
```

### Launching the Interactive Web Dashboard
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 2. Web Dashboard Guide

### Page 1: Overview
- Review project architecture, supported compression and data formats, and recent verification history.

### Page 2: Analyze Export
1. Select **"Select Pre-Generated Demo Dataset"** to test built-in demonstration files (Demo A to F), or choose **"Upload Custom File"**.
2. Select or confirm data format (Auto-Detect, CSV, JSON Lines, SQL Dump).
3. Optionally upload a trusted manifest JSON file.
4. Click **"🚀 Run Integrity Analysis"**.
5. Inspect the Recovery Feasibility Verdict badge, compression statistics, cryptographic checksums, chunk tables, anomalies, and inferred schema types.

### Page 3: Compare Exports (The Core Problem Statement)
1. Select or upload Baseline export (e.g. `demo_a_baseline_100k.csv.gz`).
2. Select or upload Current export (e.g. `demo_a_repetitive_130k.csv.gz`).
3. Click **"⚖️ Compare Exports Side-by-Side"**.
4. Observe the side-by-side metric table, percentage changes, compression ratio surge, and the automated explanation of why the 130k export is smaller than the 100k export.

### Page 4: Integrity Evidence
- Filter checks by status (PASS, FAIL, WARNING, INCONCLUSIVE) and review the underlying evidentiary basis and scientific caveats.

### Page 5: Manifest Manager
- **Create Manifest:** Generate versioned manifests for exports. Select whether the manifest was generated synchronously at export time (`TRUSTED_EXPORT_PIPELINE`) or after-the-fact (`OBSERVATIONAL_POST_HOC`).
- **Validate Manifest:** Verify external manifest JSON files against the DBGuard Version 1.0 schema.

### Page 6: Recovery Assessment
- View detailed breakdown of verified properties, unverified properties, estimated recoverable rows, and actionable remediation steps.

### Page 7: Benchmarks & Experiments
- Explore real measured empirical data, scalability charts, and memory comparison graphs (DBGuard vs Full In-Memory Loading).

### Page 8: Reports Download
- Download publication-quality PDF reports, tabular CSV summaries, and complete JSON audit logs.

---

## 3. Command-Line Interface (CLI) Guide

### Intake Inspection
```bash
python cli.py inspect --file sample_data/demo_a_baseline_100k.csv.gz
```

### Streaming Integrity Analysis
```bash
python cli.py analyze --file sample_data/demo_a_baseline_100k.csv.gz --format csv
```

### Export Reports from Analysis
```bash
python cli.py analyze --file sample_data/demo_e_matching_25k.csv.gz \
  --manifest manifests/demo_e_matching_25k.manifest.json \
  --output-pdf output/report.pdf \
  --output-json output/report.json \
  --output-csv output/report.csv
```

### Export Comparison
```bash
python cli.py compare \
  --old sample_data/demo_a_baseline_100k.csv.gz \
  --new sample_data/demo_a_repetitive_130k.csv.gz
```

### Manifest Generation
```bash
# Generate observational post-hoc manifest
python cli.py generate-manifest --file sample_data/demo_a_baseline_100k.csv.gz --output export.manifest.json

# Generate pipeline-trusted manifest with HMAC key
python cli.py generate-manifest --file sample_data/demo_a_baseline_100k.csv.gz --output export.manifest.json --trusted --key "SecretKey123"
```

### Manifest Verification
```bash
python cli.py verify-manifest \
  --file sample_data/demo_e_matching_25k.csv.gz \
  --manifest manifests/demo_e_matching_25k.manifest.json
```

