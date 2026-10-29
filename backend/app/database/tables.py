"""SQLAlchemy ORM tables for DBGuard application metadata."""

from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import relationship
from backend.app.database.connection import Base


class DBAnalysis(Base):
    __tablename__ = "analyses"

    id = Column(String(64), primary_key=True, index=True)
    original_filename = Column(String(255), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    compressed_size_bytes = Column(Integer, nullable=False)
    decompressed_size_bytes = Column(Integer, nullable=False)
    row_count = Column(Integer, nullable=False)
    column_count = Column(Integer, nullable=False)
    compression_format = Column(String(32), nullable=False)
    data_format = Column(String(32), nullable=False)
    compressed_sha256 = Column(String(64), nullable=False)
    decompressed_sha256 = Column(String(64), nullable=True)
    schema_fingerprint = Column(String(64), nullable=True)
    analysis_status = Column(String(32), nullable=False)
    recovery_assessment = Column(String(64), nullable=False)
    recovery_summary = Column(Text, nullable=False)
    execution_duration_sec = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    full_report_json = Column(Text, nullable=False)

    checks = relationship("DBIntegrityCheck", back_populates="analysis", cascade="all, delete-orphan")
    anomalies = relationship("DBAnomaly", back_populates="analysis", cascade="all, delete-orphan")


class DBIntegrityCheck(Base):
    __tablename__ = "integrity_checks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(64), ForeignKey("analyses.id"), nullable=False, index=True)
    category = Column(String(64), nullable=False)
    check_name = Column(String(128), nullable=False)
    status = Column(String(32), nullable=False)
    observed_value = Column(Text, nullable=True)
    expected_value = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    evidence_reference = Column(Text, nullable=True)

    analysis = relationship("DBAnalysis", back_populates="checks")


class DBAnomaly(Base):
    __tablename__ = "anomalies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    analysis_id = Column(String(64), ForeignKey("analyses.id"), nullable=False, index=True)
    rule_id = Column(String(64), nullable=False)
    severity = Column(String(32), nullable=False)
    metric_name = Column(String(64), nullable=False)
    observed_value = Column(Text, nullable=True)
    expected_value = Column(Text, nullable=True)
    explanation = Column(Text, nullable=False)
    recommendation = Column(Text, nullable=False)

    analysis = relationship("DBAnalysis", back_populates="anomalies")


class DBComparison(Base):
    __tablename__ = "comparisons"

    id = Column(String(64), primary_key=True, index=True)
    previous_filename = Column(String(255), nullable=False)
    current_filename = Column(String(255), nullable=False)
    row_count_change_pct = Column(Float, nullable=True)
    compressed_size_change_pct = Column(Float, nullable=True)
    decompressed_size_change_pct = Column(Float, nullable=True)
    compression_ratio_old = Column(Float, nullable=False)
    compression_ratio_new = Column(Float, nullable=False)
    bytes_per_row_old = Column(Float, nullable=False)
    bytes_per_row_new = Column(Float, nullable=False)
    schema_match = Column(Boolean, default=True)
    summary_verdict = Column(Text, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    full_comparison_json = Column(Text, nullable=False)


class DBBenchmark(Base):
    __tablename__ = "benchmarks"

    id = Column(String(64), primary_key=True, index=True)
    experiment = Column(String(64), nullable=False)
    scenario = Column(String(64), nullable=False)
    rows = Column(Integer, nullable=False)
    compressed_bytes = Column(Integer, nullable=False)
    decompressed_bytes = Column(Integer, nullable=False)
    duration_sec = Column(Float, nullable=False)
    peak_memory_mb = Column(Float, nullable=False)
    throughput_rec_s = Column(Float, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

