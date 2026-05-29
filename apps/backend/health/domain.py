from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class TelemetryStatus(StrEnum):
    SUCCESS = "success"
    FAILED = "failed"
    WARNING = "warning"


@dataclass
class PipelineRunTelemetry:
    """Immutable telemetry row for a single pipeline run step.

    Defined in PRD 0007:
    - Stored per run step at terminal states (success/failed).
    - Carries threshold_snapshot so historical comparisons remain stable.
    - pipeline_id follows canonical form: {job_type}:{dataset_id} or {job_type}.
    """

    id: str
    tenant_id: str
    pipeline_id: str
    job_type: str
    run_id: str
    dataset_id: str | None = None
    connection_id: str | None = None
    status: str = TelemetryStatus.SUCCESS.value
    duration_ms: int = 0
    bytes_written: int = 0
    rows_processed: int = 0
    error_message: str = ""
    warning_message: str = ""
    latency_threshold_ms: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class DailyPipelineRollup:
    """Daily aggregated rollup for a pipeline-scoped row.

    One row per (tenant_id, pipeline_id, date).
    Kept indefinitely per PRD 0007.
    """

    id: str
    tenant_id: str
    pipeline_id: str
    job_type: str
    date: str  # ISO date YYYY-MM-DD
    run_count: int = 0
    success_count: int = 0
    failed_count: int = 0
    warning_count: int = 0
    total_duration_ms: int = 0
    total_bytes_written: int = 0
    total_rows_processed: int = 0
    max_duration_ms: int = 0
    sla_violation_count: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(UTC))


ROLLUP_WINDOW_DAYS = 30


class PipelineHealthState(StrEnum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"


def derive_pipeline_health(
    today_failure_count: int,
    window_failure_count: int,
    recent_sla_violation_count: int,
) -> PipelineHealthState:
    """Derive pipeline health per PRD 0007 rules.

    - FAILED: any failure in last 24 hours
    - DEGRADED: no failures in last 24h, but SLA violation in last 7d or any failures in 30d
    - HEALTHY: otherwise
    """
    if today_failure_count > 0:
        return PipelineHealthState.FAILED
    if window_failure_count > 0:
        return PipelineHealthState.DEGRADED
    if recent_sla_violation_count > 0:
        return PipelineHealthState.DEGRADED
    return PipelineHealthState.HEALTHY
