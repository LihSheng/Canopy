from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from health.domain import PipelineRunTelemetry, derive_pipeline_health
from health.schema import DailyPipelineRollupModel, PipelineRunTelemetryModel


class TelemetryRepository:
    """Repository for pipeline_run_telemetry rows."""

    def __init__(self, db: Session):
        self._db = db

    def insert(self, telemetry: PipelineRunTelemetry) -> PipelineRunTelemetryModel:
        model = PipelineRunTelemetryModel(
            id=telemetry.id,
            tenant_id=telemetry.tenant_id,
            pipeline_id=telemetry.pipeline_id,
            job_type=telemetry.job_type,
            run_id=telemetry.run_id,
            dataset_id=telemetry.dataset_id,
            connection_id=telemetry.connection_id,
            status=telemetry.status,
            duration_ms=telemetry.duration_ms,
            bytes_written=telemetry.bytes_written,
            rows_processed=telemetry.rows_processed,
            error_message=telemetry.error_message,
            warning_message=telemetry.warning_message,
            latency_threshold_ms=telemetry.latency_threshold_ms,
            started_at=telemetry.started_at,
            finished_at=telemetry.finished_at,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return model

    def list_recent_failures(
        self,
        tenant_id: str,
        limit: int = 50,
        since: datetime | None = None,
    ) -> list[PipelineRunTelemetryModel]:
        query = self._db.query(PipelineRunTelemetryModel).filter(
            PipelineRunTelemetryModel.tenant_id == tenant_id,
            PipelineRunTelemetryModel.status == "failed",
        )
        if since:
            query = query.filter(PipelineRunTelemetryModel.created_at >= since)
        return query.order_by(PipelineRunTelemetryModel.created_at.desc()).limit(limit).all()

    def list_by_run(self, tenant_id: str, run_id: str) -> list[PipelineRunTelemetryModel]:
        return (
            self._db.query(PipelineRunTelemetryModel)
            .filter(
                PipelineRunTelemetryModel.tenant_id == tenant_id,
                PipelineRunTelemetryModel.run_id == run_id,
            )
            .order_by(PipelineRunTelemetryModel.created_at.asc())
            .all()
        )

    def list_by_pipeline(self, tenant_id: str, pipeline_id: str, limit: int = 50) -> list[PipelineRunTelemetryModel]:
        return (
            self._db.query(PipelineRunTelemetryModel)
            .filter(
                PipelineRunTelemetryModel.tenant_id == tenant_id,
                PipelineRunTelemetryModel.pipeline_id == pipeline_id,
            )
            .order_by(PipelineRunTelemetryModel.created_at.desc())
            .limit(limit)
            .all()
        )


class RollupRepository:
    """Repository for daily_pipeline_rollups."""

    def __init__(self, db: Session):
        self._db = db

    def upsert(self, rollup: dict) -> DailyPipelineRollupModel:
        """Upsert a rollup row. Returns the model."""
        existing = (
            self._db.query(DailyPipelineRollupModel)
            .filter(
                DailyPipelineRollupModel.tenant_id == rollup["tenant_id"],
                DailyPipelineRollupModel.pipeline_id == rollup["pipeline_id"],
                DailyPipelineRollupModel.date == rollup["date"],
            )
            .first()
        )
        if existing:
            existing.run_count = rollup["run_count"]
            existing.success_count = rollup["success_count"]
            existing.failed_count = rollup["failed_count"]
            existing.warning_count = rollup["warning_count"]
            existing.total_duration_ms = rollup["total_duration_ms"]
            existing.total_bytes_written = rollup["total_bytes_written"]
            existing.total_rows_processed = rollup["total_rows_processed"]
            existing.max_duration_ms = rollup["max_duration_ms"]
            existing.sla_violation_count = rollup["sla_violation_count"]
            existing.updated_at = datetime.now(UTC)
            self._db.commit()
            self._db.refresh(existing)
            return existing
        model = DailyPipelineRollupModel(
            tenant_id=rollup["tenant_id"],
            pipeline_id=rollup["pipeline_id"],
            job_type=rollup["job_type"],
            date=rollup["date"],
            run_count=rollup["run_count"],
            success_count=rollup["success_count"],
            failed_count=rollup["failed_count"],
            warning_count=rollup["warning_count"],
            total_duration_ms=rollup["total_duration_ms"],
            total_bytes_written=rollup["total_bytes_written"],
            total_rows_processed=rollup["total_rows_processed"],
            max_duration_ms=rollup["max_duration_ms"],
            sla_violation_count=rollup["sla_violation_count"],
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return model

    def get_summary(self, tenant_id: str, window_days: int = 30) -> dict:
        """Aggregate rollups into top-level KPIs for the rolling window."""
        utc_today = datetime.now(UTC).date()
        cutoff = (utc_today - timedelta(days=window_days)).isoformat()
        row = (
            self._db.query(
                func.count(DailyPipelineRollupModel.id).label("total_days"),
                func.coalesce(func.sum(DailyPipelineRollupModel.total_bytes_written), 0).label("total_bytes_written"),
                func.coalesce(func.sum(DailyPipelineRollupModel.failed_count), 0).label("total_failures"),
                func.coalesce(func.sum(DailyPipelineRollupModel.warning_count), 0).label("total_warnings"),
                func.coalesce(func.sum(DailyPipelineRollupModel.sla_violation_count), 0).label("total_sla_violations"),
                func.coalesce(func.sum(DailyPipelineRollupModel.run_count), 0).label("total_runs"),
                func.count(func.distinct(DailyPipelineRollupModel.pipeline_id)).label("active_pipeline_count"),
            )
            .filter(
                DailyPipelineRollupModel.tenant_id == tenant_id,
                DailyPipelineRollupModel.date >= cutoff,
            )
            .first()
        )
        return {
            "total_bytes_written": int(row.total_bytes_written) if row else 0,
            "total_failures": int(row.total_failures) if row else 0,
            "total_warnings": int(row.total_warnings) if row else 0,
            "total_sla_violations": int(row.total_sla_violations) if row else 0,
            "total_runs": int(row.total_runs) if row else 0,
            "active_pipeline_count": int(row.active_pipeline_count) if row else 0,
        }

    def get_trends(self, tenant_id: str, window_days: int = 30) -> list[dict]:
        """Daily trend data for charts."""
        utc_today = datetime.now(UTC).date()
        cutoff = (utc_today - timedelta(days=window_days)).isoformat()
        rows = (
            self._db.query(
                DailyPipelineRollupModel.date,
                func.coalesce(func.sum(DailyPipelineRollupModel.total_bytes_written), 0).label("bytes_written"),
                func.coalesce(func.sum(DailyPipelineRollupModel.failed_count), 0).label("errors"),
                func.coalesce(func.sum(DailyPipelineRollupModel.sla_violation_count), 0).label("sla_violations"),
                func.coalesce(func.sum(DailyPipelineRollupModel.run_count), 0).label("run_count"),
            )
            .filter(
                DailyPipelineRollupModel.tenant_id == tenant_id,
                DailyPipelineRollupModel.date >= cutoff,
            )
            .group_by(DailyPipelineRollupModel.date)
            .order_by(DailyPipelineRollupModel.date.asc())
            .all()
        )
        return [
            {
                "date": r.date,
                "bytes_written": int(r.bytes_written),
                "errors": int(r.errors),
                "sla_violations": int(r.sla_violations),
                "run_count": int(r.run_count),
            }
            for r in rows
        ]

    def get_pipeline_catalog(self, tenant_id: str, window_days: int = 30) -> list[dict]:
        """List all pipelines with aggregated stats and derived health state."""
        utc_today = datetime.now(UTC).date()
        cutoff = (utc_today - timedelta(days=window_days)).isoformat()
        today = utc_today.isoformat()
        seven_days_ago = (utc_today - timedelta(days=7)).isoformat()

        # Get aggregate stats per pipeline
        rows = (
            self._db.query(
                DailyPipelineRollupModel.pipeline_id,
                DailyPipelineRollupModel.job_type,
                func.coalesce(func.sum(DailyPipelineRollupModel.run_count), 0).label("total_runs"),
                func.coalesce(func.sum(DailyPipelineRollupModel.failed_count), 0).label("total_failures"),
                func.coalesce(func.sum(DailyPipelineRollupModel.total_bytes_written), 0).label("total_bytes_written"),
                func.coalesce(func.sum(DailyPipelineRollupModel.sla_violation_count), 0).label("total_sla_violations"),
                func.coalesce(func.max(DailyPipelineRollupModel.max_duration_ms), 0).label("max_duration_ms"),
            )
            .filter(
                DailyPipelineRollupModel.tenant_id == tenant_id,
                DailyPipelineRollupModel.date >= cutoff,
            )
            .group_by(DailyPipelineRollupModel.pipeline_id, DailyPipelineRollupModel.job_type)
            .all()
        )

        # Today's failure count per pipeline to determine health
        today_failures_raw = (
            self._db.query(
                DailyPipelineRollupModel.pipeline_id,
                func.coalesce(func.sum(DailyPipelineRollupModel.failed_count), 0).label("today_failures"),
            )
            .filter(
                DailyPipelineRollupModel.tenant_id == tenant_id,
                DailyPipelineRollupModel.date >= today,
            )
            .group_by(DailyPipelineRollupModel.pipeline_id)
            .all()
        )
        today_failures_map = {r.pipeline_id: int(r.today_failures) for r in today_failures_raw}

        # SLA violations in last 7 days per pipeline
        recent_sla_raw = (
            self._db.query(
                DailyPipelineRollupModel.pipeline_id,
                func.coalesce(func.sum(DailyPipelineRollupModel.sla_violation_count), 0).label("recent_sla"),
            )
            .filter(
                DailyPipelineRollupModel.tenant_id == tenant_id,
                DailyPipelineRollupModel.date >= seven_days_ago,
                DailyPipelineRollupModel.sla_violation_count > 0,
            )
            .group_by(DailyPipelineRollupModel.pipeline_id)
            .all()
        )
        recent_sla_map = {r.pipeline_id: int(r.recent_sla) for r in recent_sla_raw}

        catalog = []
        for r in rows:
            pid = r.pipeline_id
            today_fails = today_failures_map.get(pid, 0)
            recent_sla = recent_sla_map.get(pid, 0)
            total_fails = int(r.total_failures)

            health = derive_pipeline_health(
                today_failure_count=int(today_fails),
                window_failure_count=total_fails,
                recent_sla_violation_count=int(recent_sla),
            ).value

            catalog.append(
                {
                    "pipeline_id": pid,
                    "job_type": r.job_type,
                    "health": health,
                    "total_runs": int(r.total_runs),
                    "total_failures": total_fails,
                    "total_bytes_written": int(r.total_bytes_written),
                    "total_sla_violations": int(r.total_sla_violations),
                    "max_duration_ms": int(r.max_duration_ms),
                }
            )

        catalog.sort(key=lambda p: ({"failed": 0, "degraded": 1, "healthy": 2}[p["health"]], p["pipeline_id"]))
        return catalog

    def get_pipeline_detail(self, tenant_id: str, pipeline_id: str, window_days: int = 30) -> dict | None:
        """Get 30-day summary for a specific pipeline."""
        utc_today = datetime.now(UTC).date()
        cutoff = (utc_today - timedelta(days=window_days)).isoformat()
        row = (
            self._db.query(
                DailyPipelineRollupModel.pipeline_id,
                DailyPipelineRollupModel.job_type,
                func.count(DailyPipelineRollupModel.id).label("days_active"),
                func.coalesce(func.sum(DailyPipelineRollupModel.run_count), 0).label("total_runs"),
                func.coalesce(func.sum(DailyPipelineRollupModel.failed_count), 0).label("total_failures"),
                func.coalesce(func.sum(DailyPipelineRollupModel.success_count), 0).label("total_successes"),
                func.coalesce(func.sum(DailyPipelineRollupModel.warning_count), 0).label("total_warnings"),
                func.coalesce(func.sum(DailyPipelineRollupModel.total_bytes_written), 0).label("total_bytes_written"),
                func.coalesce(func.sum(DailyPipelineRollupModel.total_rows_processed), 0).label("total_rows_processed"),
                func.coalesce(func.sum(DailyPipelineRollupModel.sla_violation_count), 0).label("total_sla_violations"),
                func.coalesce(
                    func.avg(
                        func.nullif(DailyPipelineRollupModel.total_duration_ms, 0)
                        / func.nullif(DailyPipelineRollupModel.run_count, 0)
                    ),
                    0,
                ).label("avg_duration_ms"),
                func.coalesce(func.max(DailyPipelineRollupModel.max_duration_ms), 0).label("max_duration_ms"),
            )
            .filter(
                DailyPipelineRollupModel.tenant_id == tenant_id,
                DailyPipelineRollupModel.pipeline_id == pipeline_id,
                DailyPipelineRollupModel.date >= cutoff,
            )
            .group_by(DailyPipelineRollupModel.pipeline_id, DailyPipelineRollupModel.job_type)
            .first()
        )
        if not row:
            return None
        return {
            "pipeline_id": row.pipeline_id,
            "job_type": row.job_type,
            "days_active": int(row.days_active),
            "total_runs": int(row.total_runs),
            "total_failures": int(row.total_failures),
            "total_successes": int(row.total_successes),
            "total_warnings": int(row.total_warnings),
            "total_bytes_written": int(row.total_bytes_written),
            "total_rows_processed": int(row.total_rows_processed),
            "total_sla_violations": int(row.total_sla_violations),
            "avg_duration_ms": float(row.avg_duration_ms) if row.avg_duration_ms else 0,
            "max_duration_ms": int(row.max_duration_ms),
        }
