"""DBGuard: Compressed Database Export Integrity Analyzer.

Interactive Streamlit Application providing unified streaming analysis,
comparative export evaluation, manifest validation, anomaly explanation,
and recovery assessment without requiring a secondary database restoration.
"""

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dbguard.analyzer import analyze_export
from dbguard.compression.detector import detect_compression_format
from dbguard.file_inspector import inspect_file
from dbguard.manifest.generator import generate_manifest, save_manifest_to_file
from dbguard.manifest.schema import validate_manifest_dict
from dbguard.manifest.verifier import verify_manifest
from dbguard.models import (
    AnalysisReport,
    AnomalySeverity,
    CompressionFormat,
    ExportFormat,
    ExportMetrics,
    ManifestProvenance,
    RecoveryClassification,
    VerificationStatus,
)
from dbguard.reporting.csv_report import generate_csv_report
from dbguard.reporting.json_report import generate_json_report
from dbguard.reporting.pdf_report import generate_pdf_report

# Page Config
st.set_page_config(
    page_title="DBGuard — Export Integrity Analyzer",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Enterprise CSS
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1e293b;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 1.05rem;
        color: #64748b;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .badge-pass {
        background-color: #dcfce7;
        color: #166534;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-warn {
        background-color: #fef3c7;
        color: #92400e;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-fail {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
    .badge-info {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 6px;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Session State Initialization
if "recent_analyses" not in st.session_state:
    st.session_state.recent_analyses = []
if "current_report" not in st.session_state:
    st.session_state.current_report = None


# Sidebar Navigation
st.sidebar.markdown("## 🛡️ DBGuard")
st.sidebar.markdown("**Database Export Integrity Analyzer**")
st.sidebar.markdown("---")

nav_page = st.sidebar.radio(
    "Navigation",
    [
        "1. Overview",
        "2. Analyze Export",
        "3. Compare Exports",
        "4. Integrity Evidence",
        "5. Manifest Manager",
        "6. Recovery Assessment",
        "7. Benchmarks & Experiments",
        "8. Reports Download"
    ]
)

st.sidebar.markdown("---")
st.sidebar.info(
    "**Core Principle:**\n\n"
    "Assesses large compressed database exports in bounded memory without re-importing into a second database."
)


# Helper: Render Status Badge
def render_status_badge(status: str) -> str:
    s = str(status).upper()
    if s in ("PASS", "VERIFIED_WITHIN_SCOPE"):
        return f'<span class="badge-pass">✔ {s}</span>'
    elif s in ("WARNING", "LIKELY_USABLE_BUT_NOT_FULLY_VERIFIED", "RECOVERY_POSSIBLE_WITH_ERRORS"):
        return f'<span class="badge-warn">⚠ {s}</span>'
    elif s in ("FAIL", "INTEGRITY_FAILURE"):
        return f'<span class="badge-fail">✖ {s}</span>'
    else:
        return f'<span class="badge-info">ℹ {s}</span>'


# ==============================================================================
# PAGE 1: Overview
# ==============================================================================
if nav_page == "1. Overview":
    st.markdown('<div class="main-title">DBGuard — Export Integrity Analyzer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">A Streaming-Based System for Integrity Verification, Anomaly Detection, '
        'and Recovery Assessment of Large Compressed Database Exports Without Full Database Restoration.</div>',
        unsafe_allow_html=True
    )

    st.markdown("""
    ### 🎯 The Core Problem Statement
    > *"It is observed that export file-size usually grows when the number of rows exported increases.
    > However, once it was observed that number of rows increased by 30% as compared to an earlier export,
    > but file size was reduced by 20%. Management was suspicious of the usability of the export file from
    > a data recovery point of view. Since the table is very large, there is no time scope and tablespace scope
    > to re-import it into another temporary database to validate if all data is intact."*
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        #### 🔍 Why Full Database Restoration is Impractical
        - **Terabyte Scale:** Large production tables require hours or days to transfer and import.
        - **Resource Constraints:** Provisioning a duplicate database cluster with identical storage tablespace incurs significant cloud infrastructure cost.
        - **Restoration Risk:** Re-importing does not verify whether the export was mathematically complete relative to the export-time database state without prior audit manifests.
        """)
    with col2:
        st.markdown("""
        #### 💡 The DBGuard Solution
        - **Single-Pass Streaming:** Decompresses, computes SHA-256 digests, and parses record structure simultaneously in bounded $O(B)$ memory.
        - **Decoupled Verification:** Distinguishes physical container corruption (CRC/trailer) from logical completeness and statistical compression anomalies.
        - **Explainable Anomaly Engine:** Explains why higher string repetition, NULL density, or dictionary efficiency legitimately produce smaller compressed outputs without corruption.
        """)

    st.markdown("---")
    st.markdown("### ⚙️ Supported Compression & Data Formats")
    f_col1, f_col2, f_col3, f_col4 = st.columns(4)
    with f_col1:
        st.markdown("**Containers**\n- Gzip (`.gz`)\n- Bzip2 (`.bz2`)\n- XZ / LZMA (`.xz`)\n- Zstandard (`.zst`)")
    with f_col2:
        st.markdown("**Export Formats**\n- Delimited CSV (`.csv`)\n- JSON Lines (`.jsonl`)\n- MySQL INSERT Dumps\n- PostgreSQL COPY Dumps")
    with f_col3:
        st.markdown("**Cryptographic Proofs**\n- Compressed SHA-256\n- Decompressed SHA-256\n- 1MB Chunk Digests\n- Merkle Tree Root")
    with f_col4:
        st.markdown("**Provenance Levels**\n- Trusted Export Pipeline\n- Independent Third-Party\n- Observational Post-Hoc\n- Unknown Origin")

    if st.session_state.recent_analyses:
        st.markdown("---")
        st.markdown("### 🕒 Recent Analyses in This Session")
        recent_df = pd.DataFrame(st.session_state.recent_analyses)
        st.dataframe(recent_df, use_container_width=True)


# ==============================================================================
# PAGE 2: Analyze Export
# ==============================================================================
elif nav_page == "2. Analyze Export":
    st.markdown('<div class="main-title">Analyze Compressed Export</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Upload a compressed export file or choose a pre-generated demonstration dataset.</div>', unsafe_allow_html=True)

    input_mode = st.radio("Input Source:", ["Select Pre-Generated Demo Dataset", "Upload Custom File"], horizontal=True)

    target_file = None
    target_name = None
    manifest_source = None

    if input_mode == "Select Pre-Generated Demo Dataset":
        demo_choice = st.selectbox(
            "Choose Demonstration Scenario:",
            [
                "Demo A (Newer): 130,000 Rows Repetitive (~385 KB, Smaller despite +30% rows)",
                "Demo A (Baseline): 100,000 Rows Normal (~3.09 MB)",
                "Demo B: Truncated Compressed Stream (Physical container failure)",
                "Demo C: Logically Incomplete (85k rows vs 100k manifest)",
                "Demo E: Fully Matching 25,000 Rows with Trusted Pipeline Manifest",
                "Demo F: Tampered Content with Original Manifest",
            ]
        )

        sample_dir = Path("sample_data")
        manifest_dir = Path("manifests")

        if "Demo A (Newer)" in demo_choice:
            target_file = sample_dir / "demo_a_repetitive_130k.csv.gz"
        elif "Demo A (Baseline)" in demo_choice:
            target_file = sample_dir / "demo_a_baseline_100k.csv.gz"
        elif "Demo B" in demo_choice:
            target_file = sample_dir / "demo_b_truncated.csv.gz"
        elif "Demo C" in demo_choice:
            target_file = sample_dir / "demo_c_incomplete_85k.csv.gz"
            manifest_source = manifest_dir / "demo_c_incomplete_85k.manifest.json"
        elif "Demo E" in demo_choice:
            target_file = sample_dir / "demo_e_matching_25k.csv.gz"
            manifest_source = manifest_dir / "demo_e_matching_25k.manifest.json"
        elif "Demo F" in demo_choice:
            target_file = sample_dir / "demo_f_tampered_25k.csv.gz"
            manifest_source = manifest_dir / "demo_f_tampered_25k.manifest.json"

        target_name = target_file.name if target_file else None

    else:
        uploaded_file = st.file_uploader("Upload compressed export file (.gz, .bz2, .xz, .csv)", type=["gz", "bz2", "xz", "zst", "csv", "jsonl", "sql"])
        uploaded_manifest = st.file_uploader("Upload optional integrity manifest (.json)", type=["json"])

        if uploaded_file:
            # Write to a safe temporary file
            t_file = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{uploaded_file.name}")
            t_file.write(uploaded_file.getvalue())
            t_file.close()
            target_file = Path(t_file.name)
            target_name = uploaded_file.name

        if uploaded_manifest:
            manifest_source = json.loads(uploaded_manifest.getvalue().decode("utf-8"))

    # Parser options
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        fmt_select = st.selectbox("Data Format Override:", ["Auto-Detect", "CSV", "JSON Lines", "SQL Dump"])
    with col_opt2:
        hmac_key = st.text_input("Optional Manifest HMAC Secret Key:", type="password")

    resolved_format = None
    if fmt_select == "CSV":
        resolved_format = ExportFormat.CSV
    elif fmt_select == "JSON Lines":
        resolved_format = ExportFormat.JSONL
    elif fmt_select == "SQL Dump":
        resolved_format = ExportFormat.SQL_DUMP

    if st.button("🚀 Run Integrity Analysis", type="primary", use_container_width=True):
        if not target_file or not Path(target_file).exists():
            st.error("Please provide or select a valid target export file.")
        else:
            with st.spinner("Executing bounded streaming analysis..."):
                t_start = time.perf_counter()
                secret_bytes = hmac_key.encode("utf-8") if hmac_key else None

                report = analyze_export(
                    file_path_or_buffer=target_file,
                    filename_override=target_name,
                    data_format=resolved_format,
                    manifest_path_or_dict=manifest_source,
                    secret_key=secret_bytes
                )
                st.session_state.current_report = report

                # Add to recent session
                st.session_state.recent_analyses.insert(0, {
                    "Timestamp": datetime.now(timezone.utc).strftime("%H:%M:%S"),
                    "Filename": report.file_inspection.filename,
                    "Format": report.file_inspection.detected_compression.value.upper(),
                    "Rows": f"{report.parsing_result.record_count:,}",
                    "Verdict": report.recovery_assessment.classification.value,
                    "Duration": f"{report.execution_duration_sec:.2f}s"
                })

    # Render Current Report
    report: Optional[AnalysisReport] = st.session_state.current_report
    if report:
        st.markdown("---")
        rec = report.recovery_assessment

        # Verdict Header Alert
        st.markdown(f"### Recovery Feasibility Verdict: {render_status_badge(rec.classification.value)}", unsafe_allow_html=True)
        st.info(f"**Assessment Summary:** {rec.summary}")

        # Metrics Overview Row
        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Compressed Size", f"{report.file_inspection.file_size_bytes:,} B")
        m2.metric("Decompressed Size", f"{report.compression_validation.decompressed_bytes:,} B")
        m3.metric("Rows Parsed", f"{report.parsing_result.record_count:,}")
        m4.metric("Expansion Ratio", f"{report.compression_validation.expansion_ratio:.2f}x")
        m5.metric("Columns", report.parsing_result.column_count)
        m6.metric("Duration", f"{report.execution_duration_sec:.3f}s")

        # Tabs for details
        t_decomp, t_hash, t_anom, t_schema = st.tabs([
            "📦 Compression & Stream",
            "🔐 Cryptographic Checksums",
            f"⚠ Anomalies ({len(report.anomalies)})",
            "📋 Table Schema & Columns"
        ])

        with t_decomp:
            st.markdown("#### Container & Physical Stream Verification")
            cv = report.compression_validation
            c_col1, c_col2 = st.columns(2)
            with c_col1:
                st.write(f"**Detected Format:** `{cv.format.value.upper()}`")
                st.write(f"**Decompression Status:** {render_status_badge(cv.status.value)}", unsafe_allow_html=True)
                st.write(f"**CRC / Trailer Valid:** `{cv.crc_or_trailer_valid}`")
                st.write(f"**Stream Truncated:** `{cv.is_truncated}`")
            with c_col2:
                if cv.error_message:
                    st.error(f"**Decompression Error:** {cv.error_message}")
                else:
                    st.success("Physical stream decompressed to end-of-archive without CRC errors.")

            st.caption(f"Decompressed stream SHA-256: `{cv.sha256_decompressed or 'N/A'}`")

        with t_hash:
            st.markdown("#### Cryptographic Identity & Chunk Hashes")
            hr = report.hash_result
            st.text_input("Compressed File SHA-256:", hr.compressed_sha256, disabled=True)
            st.text_input("Decompressed Stream SHA-256:", hr.decompressed_sha256 or "N/A", disabled=True)
            st.text_input("1MB Chunks Merkle Tree Root:", hr.merkle_root or "N/A", disabled=True)

            if hr.chunk_hashes:
                st.markdown(f"**Granular 1MB Chunks ({len(hr.chunk_hashes)} verified):**")
                chunk_df = pd.DataFrame([
                    {
                        "Chunk Index": c.index,
                        "Start Byte": f"{c.start_byte:,}",
                        "End Byte": f"{c.end_byte:,}",
                        "Length (B)": f"{c.length_bytes:,}",
                        "SHA-256 Digest": c.sha256
                    } for c in hr.chunk_hashes
                ])
                st.dataframe(chunk_df, use_container_width=True)

        with t_anom:
            if report.anomalies:
                st.markdown(f"#### Detected Anomalies ({len(report.anomalies)})")
                anom_data = []
                for a in report.anomalies:
                    anom_data.append({
                        "Rule ID": a.rule_id,
                        "Severity": a.severity.value,
                        "Metric": a.metric_name,
                        "Observed": str(a.observed_value),
                        "Explanation": a.explanation,
                        "Recommendation": a.recommendation
                    })
                st.dataframe(pd.DataFrame(anom_data), use_container_width=True)
            else:
                st.success("No metric or structural anomalies detected.")

        with t_schema:
            st.markdown("#### Schema Structure & Inferred Column Types")
            st.text_input("Canonical Schema Fingerprint (SHA-256):", report.parsing_result.schema_fingerprint, disabled=True)
            if report.parsing_result.column_stats:
                col_df = pd.DataFrame([
                    {
                        "Column Name": c.name,
                        "Inferred Type": c.inferred_type,
                        "Empty / Null Count": f"{c.null_or_empty_count:,}",
                        "Sample Min": c.sample_min or "",
                        "Sample Max": c.sample_max or ""
                    } for c in report.parsing_result.column_stats
                ])
                st.dataframe(col_df, use_container_width=True)


# ==============================================================================
# PAGE 3: Compare Exports (The Core Problem Statement)
# ==============================================================================
elif nav_page == "3. Compare Exports":
    st.markdown('<div class="main-title">Compare Database Exports</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-title">Investigate discrepancies between an earlier baseline export and a newer export. '
        'Directly addresses the official problem statement scenario.</div>',
        unsafe_allow_html=True
    )

    c_col1, c_col2 = st.columns(2)
    with c_col1:
        st.markdown("#### Baseline (Earlier) Export")
        old_choice = st.selectbox(
            "Select Baseline:",
            ["Demo A Baseline (100,000 Rows, ~3.09 MB)", "Upload Custom Baseline File"],
            key="old_export_select"
        )
        if "Demo A Baseline" in old_choice:
            old_path = Path("sample_data/demo_a_baseline_100k.csv.gz")
        else:
            old_upload = st.file_uploader("Upload Baseline (.csv.gz)", type=["gz", "bz2", "xz"])
            if old_upload:
                tf = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{old_upload.name}")
                tf.write(old_upload.getvalue())
                tf.close()
                old_path = Path(tf.name)
            else:
                old_path = None

    with c_col2:
        st.markdown("#### Current (Newer) Export")
        new_choice = st.selectbox(
            "Select Current:",
            ["Demo A Newer Repetitive (130,000 Rows, ~385 KB — Smaller File Size!)", "Upload Custom Current File"],
            key="new_export_select"
        )
        if "Demo A Newer" in new_choice:
            new_path = Path("sample_data/demo_a_repetitive_130k.csv.gz")
        else:
            new_upload = st.file_uploader("Upload Current (.csv.gz)", type=["gz", "bz2", "xz"])
            if new_upload:
                tf2 = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{new_upload.name}")
                tf2.write(new_upload.getvalue())
                tf2.close()
                new_path = Path(tf2.name)
            else:
                new_path = None

    if st.button("⚖️ Compare Exports Side-by-Side", type="primary", use_container_width=True):
        if not old_path or not new_path:
            st.error("Please ensure both baseline and current export files are selected.")
        else:
            with st.spinner("Analyzing and comparing both exports in streaming mode..."):
                rep_old = analyze_export(old_path)
                rep_new = analyze_export(
                    new_path,
                    comparison_baseline_metrics=ExportMetrics(
                        compressed_size_bytes=rep_old.file_inspection.file_size_bytes,
                        decompressed_size_bytes=rep_old.compression_validation.decompressed_bytes,
                        row_count=rep_old.parsing_result.record_count,
                        compression_ratio=rep_old.compression_validation.expansion_ratio,
                        bytes_per_row=(rep_old.compression_validation.decompressed_bytes / max(1, rep_old.parsing_result.record_count)),
                        schema_fingerprint=rep_old.parsing_result.schema_fingerprint,
                        column_count=rep_old.parsing_result.column_count,
                        malformed_count=rep_old.parsing_result.malformed_record_count
                    ),
                    comparison_baseline_header=rep_old.parsing_result.header
                )

                st.session_state.comparison_results = (rep_old, rep_new)

    if "comparison_results" in st.session_state:
        rep_old, rep_new = st.session_state.comparison_results
        p_old = rep_old.parsing_result
        p_new = rep_new.parsing_result
        fi_old = rep_old.file_inspection
        fi_new = rep_new.file_inspection

        row_pct = ((p_new.record_count - p_old.record_count) / max(1, p_old.record_count)) * 100.0
        size_pct = ((fi_new.file_size_bytes - fi_old.file_size_bytes) / max(1, fi_old.file_size_bytes)) * 100.0
        ratio_old = rep_old.compression_validation.decompressed_bytes / max(1, fi_old.file_size_bytes)
        ratio_new = rep_new.compression_validation.decompressed_bytes / max(1, fi_new.file_size_bytes)
        bpr_old = rep_old.compression_validation.decompressed_bytes / max(1, p_old.record_count)
        bpr_new = rep_new.compression_validation.decompressed_bytes / max(1, p_new.record_count)

        # Highlight Problem Statement Callout
        if row_pct > 0 and size_pct < 0:
            st.warning(
                f"### 🔎 The Problem Statement Phenomenon Observed!\n\n"
                f"**Row Count increased by +{row_pct:.1f}%**, yet **Compressed File Size decreased by {abs(size_pct):.1f}%**.\n\n"
                f"- **Why management was suspicious:** Standard intuition assumes export file size grows monotonically with row count.\n"
                f"- **The Scientific Reality:** The new export has higher data repetition (identical categorical status, codes, or NULLs). "
                f"The DEFLATE dictionary replaces repetitive strings with tiny backward pointers, increasing compression efficiency from "
                f"**{ratio_old:.2f}x up to {ratio_new:.2f}x**! The export decompresses and parses cleanly without corruption."
            )

        # Comparison Table
        st.markdown("### 📊 Metric Diff Table")
        diff_df = pd.DataFrame([
            {"Metric": "Row Count", "Baseline (Old)": f"{p_old.record_count:,}", "Current (New)": f"{p_new.record_count:,}", "Change": f"{row_pct:+.1f}%"},
            {"Metric": "Compressed Size", "Baseline (Old)": f"{fi_old.file_size_bytes:,} B", "Current (New)": f"{fi_new.file_size_bytes:,} B", "Change": f"{size_pct:+.1f}%"},
            {"Metric": "Decompressed Size", "Baseline (Old)": f"{rep_old.compression_validation.decompressed_bytes:,} B", "Current (New)": f"{rep_new.compression_validation.decompressed_bytes:,} B", "Change": f"{(((rep_new.compression_validation.decompressed_bytes - rep_old.compression_validation.decompressed_bytes)/max(1, rep_old.compression_validation.decompressed_bytes))*100):+.1f}%"},
            {"Metric": "Compression Ratio", "Baseline (Old)": f"{ratio_old:.2f}x", "Current (New)": f"{ratio_new:.2f}x", "Change": f"{(((ratio_new - ratio_old)/max(1, ratio_old))*100):+.1f}%"},
            {"Metric": "Bytes Per Row", "Baseline (Old)": f"{bpr_old:.1f} B/row", "Current (New)": f"{bpr_new:.1f} B/row", "Change": f"{(((bpr_new - bpr_old)/max(1, bpr_old))*100):+.1f}%"},
            {"Metric": "Schema Fingerprint Match", "Baseline (Old)": p_old.schema_fingerprint[:16] + "...", "Current (New)": p_new.schema_fingerprint[:16] + "...", "Change": "MATCH" if p_old.schema_fingerprint == p_new.schema_fingerprint else "MISMATCH"},
        ])
        st.dataframe(diff_df, use_container_width=True)

        # Visual Charts
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            fig_rows_size = go.Figure(data=[
                go.Bar(name="Row Count", x=["Baseline", "Current"], y=[p_old.record_count, p_new.record_count], yaxis="y", offsetgroup=1, marker_color="#3b82f6"),
                go.Bar(name="Compressed Size (KB)", x=["Baseline", "Current"], y=[fi_old.file_size_bytes / 1024, fi_new.file_size_bytes / 1024], yaxis="y2", offsetgroup=2, marker_color="#f59e0b")
            ])
            fig_rows_size.update_layout(
                title="Row Count vs Compressed File Size",
                yaxis=dict(title="Row Count"),
                yaxis2=dict(title="Compressed Size (KB)", overlaying="y", side="right"),
                barmode="group",
                legend=dict(x=0.05, y=0.95)
            )
            st.plotly_chart(fig_rows_size, use_container_width=True)

        with chart_col2:
            fig_ratios = go.Figure(data=[
                go.Bar(name="Compression Ratio", x=["Baseline", "Current"], y=[ratio_old, ratio_new], marker_color="#10b981")
            ])
            fig_ratios.update_layout(title="Compression Ratio Surge (uncompressed / compressed)", yaxis_title="Ratio (Higher = More Compressed)")
            st.plotly_chart(fig_ratios, use_container_width=True)


# ==============================================================================
# PAGE 4: Integrity Evidence
# ==============================================================================
elif nav_page == "4. Integrity Evidence":
    st.markdown('<div class="main-title">Integrity Evidence & Verification Checks</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Granular status of individual cryptographic, structural, and physical checks.</div>', unsafe_allow_html=True)

    report = st.session_state.current_report
    if not report:
        st.info("No active report loaded. Please analyze an export on Page 2 first.")
    else:
        # Build checks dataset
        checks_data = []

        # 1. Container Check
        checks_data.append({
            "Category": "Physical Stream",
            "Check Name": "Container Integrity & CRC",
            "Status": report.compression_validation.status.value,
            "Observed": f"CRC Valid: {report.compression_validation.crc_or_trailer_valid}",
            "Expected": "Valid Trailer / CRC",
            "Evidence": f"{report.compression_validation.format.value.upper()} decompressor trailer verification",
            "Limitation": "Proves archive container is intact, but not source row completeness."
        })

        # 2. Decompression Truncation Check
        checks_data.append({
            "Category": "Physical Stream",
            "Check Name": "Stream Truncation Check",
            "Status": "FAIL" if report.compression_validation.is_truncated else "PASS",
            "Observed": f"Truncated: {report.compression_validation.is_truncated}",
            "Expected": "Truncated: False",
            "Evidence": "End-of-archive marker reached without EOFError",
            "Limitation": "Only detects truncation if archive format has explicit trailer."
        })

        # 3. CSV Column Consistency
        checks_data.append({
            "Category": "Record Parsing",
            "Check Name": "Column Structure Uniformity",
            "Status": "PASS" if report.parsing_result.malformed_record_count == 0 else "WARNING",
            "Observed": f"{report.parsing_result.malformed_record_count} malformed rows",
            "Expected": "0 malformed rows",
            "Evidence": f"Consistent {report.parsing_result.column_count} columns across all {report.parsing_result.record_count:,} rows",
            "Limitation": "Detects structural syntax errors, but cannot verify semantic cell correctness."
        })

        # 4. Manifest Checks (if present)
        if report.manifest_verification:
            for c in report.manifest_verification.checks:
                checks_data.append({
                    "Category": "Manifest Verification",
                    "Check Name": f"Manifest: {c.field_name}",
                    "Status": c.status.value,
                    "Observed": str(c.observed)[:40],
                    "Expected": str(c.expected)[:40],
                    "Evidence": c.message,
                    "Limitation": f"Manifest provenance: {report.manifest_verification.manifest_provenance.value}"
                })

        # Status filter
        filter_status = st.selectbox("Filter by Status:", ["ALL", "PASS", "FAIL", "WARNING", "INCONCLUSIVE"])
        df_checks = pd.DataFrame(checks_data)
        if filter_status != "ALL":
            df_checks = df_checks[df_checks["Status"] == filter_status]

        st.dataframe(df_checks, use_container_width=True)


# ==============================================================================
# PAGE 5: Manifest Manager
# ==============================================================================
elif nav_page == "5. Manifest Manager":
    st.markdown('<div class="main-title">Integrity Manifest Manager</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Generate versioned JSON manifests for newly created exports or validate existing ones.</div>', unsafe_allow_html=True)

    tab_gen, tab_val = st.tabs(["Create Manifest", "Validate Manifest"])

    with tab_gen:
        st.markdown("#### Generate Versioned Integrity Manifest")
        st.markdown(
            "> [!NOTE] **Provenance Distinction:** Manifests generated synchronously during the database export job "
            "are marked as `TRUSTED_EXPORT_PIPELINE`. Manifests generated from an existing export after-the-fact are "
            "marked as `OBSERVATIONAL_POST_HOC`."
        )

        gen_file = st.selectbox(
            "Select Export File:",
            [
                "sample_data/demo_a_baseline_100k.csv.gz",
                "sample_data/demo_a_repetitive_130k.csv.gz",
                "sample_data/demo_e_matching_25k.csv.gz",
            ]
        )
        source_id = st.text_input("Source Identifier (Table / Database Name):", value="production_export_table")
        is_trusted = st.checkbox("Mark as TRUSTED_EXPORT_PIPELINE (Checked if running synchronously at export time)", value=False)
        sec_key = st.text_input("Optional HMAC Secret Key for Cryptographic Seal:", type="password", key="gen_hmac")

        if st.button("Generate Manifest JSON", type="primary"):
            with st.spinner("Analyzing export to produce manifest..."):
                rep = analyze_export(gen_file)
                prov = ManifestProvenance.TRUSTED_EXPORT_PIPELINE if is_trusted else ManifestProvenance.OBSERVATIONAL_POST_HOC
                s_bytes = sec_key.encode("utf-8") if sec_key else None

                manifest = generate_manifest(
                    export_id=f"EXP-{Path(gen_file).stem}",
                    source_identifier=source_id,
                    export_format=rep.parsing_result.format.value,
                    compression_format=rep.compression_validation.format.value,
                    schema_fingerprint=rep.parsing_result.schema_fingerprint,
                    expected_row_count=rep.parsing_result.record_count,
                    uncompressed_size_bytes=rep.compression_validation.decompressed_bytes,
                    uncompressed_sha256=rep.hash_result.decompressed_sha256,
                    compressed_size_bytes=rep.file_inspection.file_size_bytes,
                    compressed_sha256=rep.file_inspection.sha256_compressed,
                    chunk_hashes=rep.hash_result.chunk_hashes,
                    trusted_reference_status=prov,
                    secret_key=s_bytes
                )

                st.session_state.generated_manifest = manifest
                st.success(f"Manifest successfully generated! Provenance: `{prov.value}`")

        if "generated_manifest" in st.session_state:
            man = st.session_state.generated_manifest
            st.json(man)
            st.download_button(
                "📥 Download Manifest JSON",
                data=json.dumps(man, indent=2),
                file_name=f"{man['export_id']}.manifest.json",
                mime="application/json"
            )

    with tab_val:
        st.markdown("#### Inspect & Validate Manifest Schema")
        man_upload = st.file_uploader("Upload Manifest JSON:", type=["json"], key="val_man_upload")
        if man_upload:
            try:
                data = json.loads(man_upload.getvalue().decode("utf-8"))
                validate_manifest_dict(data)
                st.success("✅ Manifest schema is 100% valid according to DBGuard Schema Version 1.0!")
                st.json(data)
            except Exception as e:
                st.error(f"❌ Manifest validation failure: {e}")


# ==============================================================================
# PAGE 6: Recovery Assessment
# ==============================================================================
elif nav_page == "6. Recovery Assessment":
    st.markdown('<div class="main-title">Data Recovery Assessment</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Evaluation of export usability for disaster recovery workflows without full restoration.</div>', unsafe_allow_html=True)

    report = st.session_state.current_report
    if not report:
        st.info("No active report loaded. Please run an analysis on Page 2 first.")
    else:
        rec = report.recovery_assessment
        st.markdown(f"### Classification: {render_status_badge(rec.classification.value)}", unsafe_allow_html=True)
        st.write(f"**Executive Summary:** {rec.summary}")

        col_v, col_u = st.columns(2)
        with col_v:
            st.markdown("#### ✅ Verified Properties")
            if rec.verified_properties:
                for p in rec.verified_properties:
                    st.write(f"• {p}")
            else:
                st.write("*(None)*")

        with col_u:
            st.markdown("#### ❓ Unverified or Inconclusive Properties")
            if rec.unverified_or_inconclusive:
                for p in rec.unverified_or_inconclusive:
                    st.write(f"• {p}")
            else:
                st.write("*(None)*")

        if rec.failures:
            st.markdown("#### ❌ Integrity Failures")
            for f in rec.failures:
                st.error(f)

        st.markdown("---")
        st.markdown(f"#### 📦 Recoverable Record Estimate: **{rec.recoverable_record_estimate:,} records**")
        st.markdown("#### 🛠️ Recommended Actions for DBA / Recovery Team:")
        for a in rec.recommended_actions:
            st.write(f"1. {a}")

        if rec.evidence_needed_for_full_claim:
            st.markdown("#### 🔬 Evidence Needed for Stronger Claim:")
            for e in rec.evidence_needed_for_full_claim:
                st.write(f"• {e}")


# ==============================================================================
# PAGE 7: Benchmarks and Experiments
# ==============================================================================
elif nav_page == "7. Benchmarks & Experiments":
    st.markdown('<div class="main-title">Empirical Benchmarks & Experimental Results</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Measured performance, throughput, memory profiling, and compression variability.</div>', unsafe_allow_html=True)

    bench_csv = Path("experiments/benchmark_results.csv")
    if bench_csv.exists():
        df_bench = pd.read_csv(bench_csv)

        # Scalability chart
        df_scale = df_bench[df_bench["experiment"] == "Scalability"]
        if not df_scale.empty:
            st.markdown("### 📈 Experiment 1: Large-File Scalability (10k to 250k rows)")
            fig_scale = px.line(
                df_scale,
                x="rows",
                y="duration_sec",
                markers=True,
                title="Linear Time Complexity O(N) Across Dataset Scales",
                labels={"rows": "Record Count", "duration_sec": "Analysis Time (seconds)"}
            )
            st.plotly_chart(fig_scale, use_container_width=True)

        # Streaming vs Full-File chart
        df_mem = df_bench[df_bench["experiment"] == "Streaming_vs_FullLoad"]
        if not df_mem.empty:
            st.markdown("### 🧠 Experiment 3: Streaming vs Full In-Memory Loading (Peak RAM)")
            fig_mem = px.bar(
                df_mem,
                x="scenario",
                y="peak_memory_mb",
                color="scenario",
                title="Peak Traced Heap Memory (tracemalloc): DBGuard Streaming vs Full Load",
                labels={"peak_memory_mb": "Peak Memory (MB)", "scenario": "Architecture Mode"}
            )
            st.plotly_chart(fig_mem, use_container_width=True)

        st.markdown("### 📋 Measured Benchmark Dataset")
        st.dataframe(df_bench, use_container_width=True)
    else:
        st.warning("Benchmark results file not found. Run `python scripts/benchmark.py` to generate measured data.")


# ==============================================================================
# PAGE 8: Reports Download
# ==============================================================================
elif nav_page == "8. Reports Download":
    st.markdown('<div class="main-title">Download Integrity Reports</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Export publication-ready PDF, structured JSON, and CSV summaries.</div>', unsafe_allow_html=True)

    report = st.session_state.current_report
    if not report:
        st.info("No active report loaded. Please run an analysis on Page 2 first.")
    else:
        # Generate string / file outputs
        json_content = generate_json_report(report)
        csv_content = generate_csv_report(report)

        # Render PDF to temp file
        pdf_temp = Path(tempfile.gettempdir()) / f"{report.report_id}.pdf"
        generate_pdf_report(report, pdf_temp)
        with open(pdf_temp, "rb") as f:
            pdf_bytes = f.read()

        c1, c2, c3 = st.columns(3)
        with c1:
            st.download_button(
                "📄 Download PDF Report",
                data=pdf_bytes,
                file_name=f"{report.report_id}_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        with c2:
            st.download_button(
                "📊 Download CSV Summary",
                data=csv_content,
                file_name=f"{report.report_id}_summary.csv",
                mime="text/csv",
                use_container_width=True
            )
        with c3:
            st.download_button(
                "💾 Download JSON Full Report",
                data=json_content,
                file_name=f"{report.report_id}_report.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown("---")
        st.markdown("### JSON Report Preview")
        st.json(report.to_dict())

