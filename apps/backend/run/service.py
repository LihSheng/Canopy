import uuid
from datetime import UTC, datetime

from health.domain import TelemetryStatus
from health.service import TelemetryService
from run.domain import Run, RunStatus
from run.repository import RunRepository


class RunService:
    def __init__(self, repo: RunRepository, telemetry_service: TelemetryService | None = None):
        self._repo = repo
        self._telemetry_service = telemetry_service

    def create_run(
        self,
        tenant_id: str,
        project_id: str,
        connection_id: str,
        dataset_id: str,
        started_by: str = "",
    ) -> Run:
        now = datetime.now(UTC)
        run = Run(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            connection_id=connection_id,
            dataset_id=dataset_id,
            status=RunStatus.QUEUED.value,
            started_by=started_by,
            created_at=now,
        )
        return self._repo.save(run)

    def update_run_status(
        self,
        run_id: str,
        status: str,
        tenant_id: str | None = None,
        error_message: str = "",
        warning_count: int = 0,
        bytes_written: int = 0,
        rows_processed: int = 0,
        latency_threshold_ms: int | None = None,
    ) -> Run:
        run = self._repo.get(run_id)
        if run is None:
            raise ValueError(f"Run {run_id} not found")
        now = datetime.now(UTC)
        run.status = status
        run.error_message = error_message
        run.warning_count = warning_count
        if status == RunStatus.RUNNING.value and run.started_at is None:
            run.started_at = now
        if status in (RunStatus.COMPLETED.value, RunStatus.FAILED.value):
            run.finished_at = now
            if run.started_at:
                run.duration_ms = int((now - run.started_at).total_seconds() * 1000)

        updated = self._repo.update(run)

        # Emit telemetry at terminal states only (PRD 0007).
        if self._telemetry_service and tenant_id and status in (RunStatus.COMPLETED.value, RunStatus.FAILED.value):
            pipeline_id = f"run:{run.dataset_id}" if run.dataset_id else "run"
            telemetry_status = (
                TelemetryStatus.FAILED.value
                if status == RunStatus.FAILED.value
                else (TelemetryStatus.WARNING.value if warning_count > 0 else TelemetryStatus.SUCCESS.value)
            )
            self._telemetry_service.record_telemetry(
                tenant_id=tenant_id,
                pipeline_id=pipeline_id,
                job_type="run",
                run_id=run_id,
                status=telemetry_status,
                dataset_id=run.dataset_id,
                connection_id=run.connection_id,
                duration_ms=run.duration_ms,
                bytes_written=bytes_written,
                rows_processed=rows_processed,
                error_message=error_message,
                warning_message="" if warning_count <= 0 else f"{warning_count} warnings",
                latency_threshold_ms=latency_threshold_ms,
                started_at=run.started_at,
                finished_at=run.finished_at,
            )
        return updated

    def get_run(self, id: str, tenant_id: str | None = None) -> Run | None:
        return self._repo.get(id, tenant_id=tenant_id)

    def list_all_runs(self, tenant_id: str | None = None) -> list[Run]:
        return self._repo.list_all(tenant_id=tenant_id)

    def list_runs_by_dataset(self, dataset_id: str, tenant_id: str | None = None) -> list[Run]:
        return self._repo.list_by_dataset(dataset_id, tenant_id=tenant_id)

    def list_runs_by_project(self, project_id: str, tenant_id: str | None = None) -> list[Run]:
        return self._repo.list_by_project(project_id, tenant_id=tenant_id)
