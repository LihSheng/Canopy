"""Unit tests for health domain logic: health derivation, status enums, dataclass invariants."""

import pytest

from health.domain import (
    DailyPipelineRollup,
    PipelineHealthState,
    PipelineRunTelemetry,
    TelemetryStatus,
    derive_pipeline_health,
)


class TestTelemetryStatus:
    """TelemetryStatus enum must match the three valid terminal states."""

    def test_status_values(self):
        assert TelemetryStatus.SUCCESS.value == "success"
        assert TelemetryStatus.FAILED.value == "failed"
        assert TelemetryStatus.WARNING.value == "warning"

    def test_status_is_string_enum(self):
        assert TelemetryStatus.SUCCESS == "success"
        assert isinstance(TelemetryStatus.SUCCESS, str)


class TestPipelineRunTelemetry:
    """PipelineRunTelemetry dataclass construction and defaults."""

    def test_minimal_construction(self):
        telemetry = PipelineRunTelemetry(
            id="t-1",
            tenant_id="tenant-1",
            pipeline_id="pipe-1",
            job_type="ingestion",
            run_id="run-1",
        )
        assert telemetry.status == TelemetryStatus.SUCCESS.value
        assert telemetry.duration_ms == 0
        assert telemetry.bytes_written == 0
        assert telemetry.rows_processed == 0
        assert telemetry.error_message == ""
        assert telemetry.warning_message == ""
        assert telemetry.latency_threshold_ms is None
        assert telemetry.started_at is None
        assert telemetry.finished_at is None
        assert telemetry.dataset_id is None
        assert telemetry.connection_id is None

    def test_full_construction(self):
        telemetry = PipelineRunTelemetry(
            id="t-2",
            tenant_id="tenant-2",
            pipeline_id="pipe-2",
            job_type="transform",
            run_id="run-2",
            dataset_id="ds-1",
            connection_id="conn-1",
            status=TelemetryStatus.FAILED.value,
            duration_ms=5000,
            bytes_written=1048576,
            rows_processed=200,
            error_message="Connection refused",
            warning_message="",
            latency_threshold_ms=3000,
        )
        assert telemetry.status == "failed"
        assert telemetry.duration_ms == 5000
        assert telemetry.error_message == "Connection refused"


class TestDailyPipelineRollup:
    """DailyPipelineRollup dataclass construction and defaults."""

    def test_default_construction(self):
        rollup = DailyPipelineRollup(
            id="r-1",
            tenant_id="tenant-1",
            pipeline_id="pipe-1",
            job_type="ingestion",
            date="2026-05-30",
        )
        assert rollup.run_count == 0
        assert rollup.success_count == 0
        assert rollup.failed_count == 0
        assert rollup.warning_count == 0
        assert rollup.total_duration_ms == 0
        assert rollup.total_bytes_written == 0
        assert rollup.total_rows_processed == 0
        assert rollup.max_duration_ms == 0
        assert rollup.sla_violation_count == 0


class TestDerivePipelineHealth:
    """derive_pipeline_health per PRD 0007 rules."""

    def test_healthy_when_no_failures_and_no_sla_violations(self):
        result = derive_pipeline_health(
            today_failure_count=0,
            window_failure_count=0,
            recent_sla_violation_count=0,
        )
        assert result == PipelineHealthState.HEALTHY

    def test_failed_when_today_failure_exists(self):
        """Any failure in last 24 hours → FAILED."""
        result = derive_pipeline_health(
            today_failure_count=1,
            window_failure_count=1,
            recent_sla_violation_count=0,
        )
        assert result == PipelineHealthState.FAILED

    def test_failed_multiple_today_failures(self):
        result = derive_pipeline_health(
            today_failure_count=5,
            window_failure_count=10,
            recent_sla_violation_count=0,
        )
        assert result == PipelineHealthState.FAILED

    def test_degraded_when_window_failures_but_none_today(self):
        """Failures in window but not today → DEGRADED."""
        result = derive_pipeline_health(
            today_failure_count=0,
            window_failure_count=3,
            recent_sla_violation_count=0,
        )
        assert result == PipelineHealthState.DEGRADED

    def test_degraded_when_recent_sla_violations_no_failures(self):
        """SLA violations in last 7d but no failures → DEGRADED."""
        result = derive_pipeline_health(
            today_failure_count=0,
            window_failure_count=0,
            recent_sla_violation_count=2,
        )
        assert result == PipelineHealthState.DEGRADED

    def test_degraded_when_sla_violations_and_window_failures_but_no_today(self):
        result = derive_pipeline_health(
            today_failure_count=0,
            window_failure_count=5,
            recent_sla_violation_count=2,
        )
        assert result == PipelineHealthState.DEGRADED

    def test_failed_takes_priority_over_degraded(self):
        """Today failure always wins over SLA violations."""
        result = derive_pipeline_health(
            today_failure_count=1,
            window_failure_count=0,
            recent_sla_violation_count=10,
        )
        assert result == PipelineHealthState.FAILED

    def test_healthy_is_default(self):
        """Zeroes across the board → HEALTHY."""
        result = derive_pipeline_health(0, 0, 0)
        assert result == PipelineHealthState.HEALTHY


class TestPipelineHealthStateEnum:
    """PipelineHealthState enum values must match API contract."""

    def test_all_states_present(self):
        states = list(PipelineHealthState)
        assert PipelineHealthState.HEALTHY in states
        assert PipelineHealthState.DEGRADED in states
        assert PipelineHealthState.FAILED in states

    def test_state_values(self):
        assert PipelineHealthState.HEALTHY.value == "healthy"
        assert PipelineHealthState.DEGRADED.value == "degraded"
        assert PipelineHealthState.FAILED.value == "failed"


class TestTelemetryServiceStatusValidation:
    """TelemetryService rejects invalid status values."""

    def test_rejects_invalid_status(self):
        from unittest.mock import MagicMock

        from health.service import TelemetryService

        svc = TelemetryService(MagicMock())
        with pytest.raises(ValueError, match="Invalid telemetry status"):
            svc.record_telemetry(
                tenant_id="t1",
                pipeline_id="p1",
                job_type="ingestion",
                run_id="r1",
                status="INVALID",
            )

    def test_accepts_valid_status(self):
        from unittest.mock import MagicMock

        from health.service import TelemetryService

        mock_db = MagicMock()
        svc = TelemetryService(mock_db)
        # Should not raise
        result = svc.record_telemetry(
            tenant_id="t1",
            pipeline_id="p1",
            job_type="ingestion",
            run_id="r1",
            status="success",
        )
        assert result is not None
