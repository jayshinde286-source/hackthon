"""Empirical benchmarks API routes."""

import csv
from datetime import datetime, timezone
import os
from pathlib import Path
import time
import tracemalloc
from typing import List

from fastapi import APIRouter
from backend.app.models.responses import BenchmarkItem
from dbguard.analyzer import analyze_export
from scripts.generate_sample_data import write_compressed_csv

router = APIRouter(prefix="/benchmarks", tags=["Benchmarks"])

BENCHMARK_CSV = Path(__file__).resolve().parent.parent.parent.parent / "experiments" / "benchmark_results.csv"


@router.get("", response_model=List[BenchmarkItem])
def get_benchmarks():
    """Retrieve measured benchmark results from empirical evaluation suite."""
    items = []
    if BENCHMARK_CSV.exists():
        with open(BENCHMARK_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                items.append(BenchmarkItem(
                    experiment=row.get("experiment", "Scalability"),
                    scenario=row.get("scenario", "default"),
                    rows=int(row.get("rows", 0)),
                    compressed_bytes=int(row.get("compressed_bytes", 0)),
                    decompressed_bytes=int(row.get("decompressed_bytes", 0)),
                    duration_sec=float(row.get("duration_sec", 0.0)),
                    peak_memory_mb=float(row.get("peak_memory_mb", 0.0)),
                    throughput_rec_s=float(row.get("throughput_rec_s", 0.0)),
                    created_at="2026-10-29T14:30:00Z"
                ))
    return items


@router.post("/run")
def run_custom_benchmark(rows: int = 25_000, repetitive: bool = False):
    """Run an on-demand benchmark with real measurement of time, memory, and throughput."""
    temp_dir = Path("/tmp/dbguard_live_bench")
    temp_dir.mkdir(parents=True, exist_ok=True)
    file_path = temp_dir / f"live_{rows}_{'rep' if repetitive else 'norm'}.csv.gz"

    try:
        comp_size = write_compressed_csv(file_path, row_count=rows, repetitive=repetitive, seed=42)

        tracemalloc.start()
        t0 = time.perf_counter()
        report = analyze_export(file_path)
        dur = round(time.perf_counter() - t0, 4)
        _, peak_mem = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        peak_mb = round(peak_mem / (1024 * 1024), 2)
        decomp_mb = round(report.compression_validation.decompressed_bytes / (1024 * 1024), 2)
        rec_s = round(rows / max(dur, 0.0001), 0)

        return {
            "experiment": "Live_Benchmark",
            "scenario": f"{rows}_rows_{'repetitive' if repetitive else 'normal'}",
            "rows": rows,
            "compressed_bytes": comp_size,
            "decompressed_bytes": report.compression_validation.decompressed_bytes,
            "duration_sec": dur,
            "peak_memory_mb": peak_mb,
            "throughput_rec_s": rec_s,
            "recovery_verdict": report.recovery_assessment.classification.value
        }
    finally:
        if file_path.exists():
            try:
                file_path.unlink()
            except Exception:
                pass

