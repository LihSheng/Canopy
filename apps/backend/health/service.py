"""Health service: telemetry ingestion, rollup building, and admin query APIs."""

import uuid
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from health.domain import PipelineRunTelemetry, TelemetryStatus
from health.repository import RollupRepository, TelemetryRepository
from health.schema import PipelineRunTelemetryModel


class TelemetryService:
    """Service for recording pipeline telemetry."""

    def __init__(self, db: Session):
        self._db = db
        self._telemetry_repo = TelemetryRepository(db)

    def record_telemetry(
        self,
        tenant_id: str,
        pipeline_id: str,
        job_type: str,
        run_id: str,
        status: str,
        dataset_id: str | None = None,
        connection_id: str | None = None,
        duration_ms: int = 0,
        bytes_written: int = 0,
        rows_processed: int = 0,
        error_message: str = "",
        warning_message: str = "",
        latency_threshold_ms: int | None = None,
        started_at: datetime | None = None,
        finished_at: datetime | None = None,
    ) -> PipelineRunTelemetryModel:
        if status not in (
            TelemetryStatus.SUCCESS.value,
            TelemetryStatus.FAILED.value,
            TelemetryStatus.WARNING.value,
        ):
            raise ValueError(f"Invalid telemetry status: {status}")
        telemetry = PipelineRunTelemetry(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            pipeline_id=pipeline_id,
            job_type=job_type,
            run_id=run_id,
            dataset_id=dataset_id,
            connection_id=connection_id,
            status=status,
            duration_ms=duration_ms,
            bytes_written=bytes_written,
            rows_processed=rows_processed,
            error_message=error_message,
            warning_message=warning_message,
            latency_threshold_ms=latency_threshold_ms,
            started_at=started_at,
            finished_at=finished_at,
        )
        return self._telemetry_repo.insert(telemetry)


class RollupService:
    """Service for computing and querying daily rollups."""

    def __init__(self, db: Session):
        self._db = db
        self._rollup_repo = RollupRepository(db)
        self._telemetry_repo = TelemetryRepository(db)

    def compute_daily_rollup(self, tenant_id: str, target_date: date | None = None) -> None:
        """Compute/refresh rollup for a single date and tenant."""
        target = target_date or datetime.now(UTC).date()
        date_str = target.isoformat()
        day_start = datetime(target.year, target.month, target.day, tzinfo=UTC)
        day_end = day_start + timedelta(days=1)

        rows = (
            self._db.query(
                PipelineRunTelemetryModel.pipeline_id,
                PipelineRunTelemetryModel.job_type,
                func.count(PipelineRunTelemetryModel.id).label("run_count"),
                func.coalesce(func.sum(case((PipelineRunTelemetryModel.status == "success", 1), else_=0)), 0).label(
                    "success_count"
                ),
                func.coalesce(func.sum(case((PipelineRunTelemetryModel.status == "failed", 1), else_=0)), 0).label(
                    "failed_count"
                ),
                func.coalesce(func.sum(case((PipelineRunTelemetryModel.status == "warning", 1), else_=0)), 0).label(
                    "warning_count"
                ),
                func.coalesce(func.sum(PipelineRunTelemetryModel.duration_ms), 0).label("total_duration_ms"),
                func.coalesce(func.sum(PipelineRunTelemetryModel.bytes_written), 0).label("total_bytes_written"),
                func.coalesce(func.sum(PipelineRunTelemetryModel.rows_processed), 0).label("total_rows_processed"),
                func.coalesce(func.max(PipelineRunTelemetryModel.duration_ms), 0).label("max_duration_ms"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                and_(
                                    PipelineRunTelemetryModel.latency_threshold_ms.isnot(None),
                                    PipelineRunTelemetryModel.duration_ms
                                    > PipelineRunTelemetryModel.latency_threshold_ms,
                                ),
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("sla_violation_count"),
            )
            .filter(
                PipelineRunTelemetryModel.tenant_id == tenant_id,
                PipelineRunTelemetryModel.created_at >= day_start,
                PipelineRunTelemetryModel.created_at < day_end,
            )
            .group_by(PipelineRunTelemetryModel.pipeline_id, PipelineRunTelemetryModel.job_type)
            .all()
        )

        for r in rows:
            self._rollup_repo.upsert(
                {
                    "tenant_id": tenant_id,
                    "pipeline_id": r.pipeline_id,
                    "job_type": r.job_type,
                    "date": date_str,
                    "run_count": int(r.run_count),
                    "success_count": int(r.success_count),
                    "failed_count": int(r.failed_count),
                    "warning_count": int(r.warning_count),
                    "total_duration_ms": int(r.total_duration_ms),
                    "total_bytes_written": int(r.total_bytes_written),
                    "total_rows_processed": int(r.total_rows_processed),
                    "max_duration_ms": int(r.max_duration_ms),
                    "sla_violation_count": int(r.sla_violation_count),
                }
            )

    def backfill(self, tenant_id: str, days: int = 30) -> None:
        """Backfill rollups for the last N days."""
        today = datetime.now(UTC).date()
        for offset in range(days, -1, -1):
            self.compute_daily_rollup(tenant_id, today - timedelta(days=offset))

    def get_summary(self, tenant_id: str, window_days: int = 30) -> dict:
        return self._rollup_repo.get_summary(tenant_id, window_days)

    def get_trends(self, tenant_id: str, window_days: int = 30) -> list[dict]:
        return self._rollup_repo.get_trends(tenant_id, window_days)

    def get_pipeline_catalog(self, tenant_id: str, window_days: int = 30) -> list[dict]:
        return self._rollup_repo.get_pipeline_catalog(tenant_id, window_days)

    def get_pipeline_detail(self, tenant_id: str, pipeline_id: str, window_days: int = 30) -> dict | None:
        return self._rollup_repo.get_pipeline_detail(tenant_id, pipeline_id, window_days)

    def get_recent_failures(self, tenant_id: str, limit: int = 50) -> list[dict]:
        models = self._telemetry_repo.list_recent_failures(tenant_id, limit)
        return [
            {
                "id": m.id,
                "run_id": m.run_id,
                "pipeline_id": m.pipeline_id,
                "job_type": m.job_type,
                "dataset_id": m.dataset_id,
                "connection_id": m.connection_id,
                "status": m.status,
                "duration_ms": m.duration_ms,
                "bytes_written": m.bytes_written,
                "rows_processed": m.rows_processed,
                "error_message": m.error_message,
                "warning_message": m.warning_message,
                "latency_threshold_ms": m.latency_threshold_ms,
                "started_at": m.started_at.isoformat() if m.started_at else None,
                "finished_at": m.finished_at.isoformat() if m.finished_at else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in models
        ]

    def get_recent_pipeline_runs(self, tenant_id: str, pipeline_id: str, limit: int = 50) -> list[dict]:
        models = self._telemetry_repo.list_by_pipeline(tenant_id, pipeline_id, limit=limit)
        return [
            {
                "id": m.id,
                "run_id": m.run_id,
                "pipeline_id": m.pipeline_id,
                "job_type": m.job_type,
                "dataset_id": m.dataset_id,
                "connection_id": m.connection_id,
                "status": m.status,
                "duration_ms": m.duration_ms,
                "bytes_written": m.bytes_written,
                "rows_processed": m.rows_processed,
                "error_message": m.error_message,
                "warning_message": m.warning_message,
                "latency_threshold_ms": m.latency_threshold_ms,
                "started_at": m.started_at.isoformat() if m.started_at else None,
                "finished_at": m.finished_at.isoformat() if m.finished_at else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in models
        ]

    def get_run_telemetry(self, tenant_id: str, run_id: str) -> list[dict]:
        models = self._telemetry_repo.list_by_run(tenant_id, run_id)
        return [
            {
                "id": m.id,
                "run_id": m.run_id,
                "pipeline_id": m.pipeline_id,
                "job_type": m.job_type,
                "dataset_id": m.dataset_id,
                "connection_id": m.connection_id,
                "status": m.status,
                "duration_ms": m.duration_ms,
                "bytes_written": m.bytes_written,
                "rows_processed": m.rows_processed,
                "error_message": m.error_message,
                "warning_message": m.warning_message,
                "latency_threshold_ms": m.latency_threshold_ms,
                "started_at": m.started_at.isoformat() if m.started_at else None,
                "finished_at": m.finished_at.isoformat() if m.finished_at else None,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in models
        ]
