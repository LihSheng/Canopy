import uuid
from datetime import UTC, datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class PipelineRunTelemetryModel(Base):
    """Immutable telemetry row for a pipeline run step (tenant-scoped)."""

    __tablename__ = "pipeline_run_telemetry"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    pipeline_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    dataset_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    connection_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="success")
    duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    bytes_written: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    rows_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    warning_message: Mapped[str] = mapped_column(Text, default="", nullable=False)
    latency_threshold_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class DailyPipelineRollupModel(Base):
    """Daily rollup row per pipeline (tenant-scoped). Kept indefinitely."""

    __tablename__ = "daily_pipeline_rollups"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    pipeline_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    job_type: Mapped[str] = mapped_column(String(100), nullable=False)
    date: Mapped[str] = mapped_column(String(10), nullable=False, index=True)  # YYYY-MM-DD
    run_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    success_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failed_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_duration_ms: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_bytes_written: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    total_rows_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    max_duration_ms: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sla_violation_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
