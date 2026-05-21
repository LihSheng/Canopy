from sqlalchemy.orm import Session

from analytics.services.monthly_aggregation_service import MonthlyAggregationService
from anomalies.service import detect_anomalies
from common.clock import utcnow
from insights.service import generate_insight
from ontology.orchestration.service import OntologyOrchestrator
from refresh.domain import STAGE_ORDER, RefreshJob, RefreshStage
from refresh.repository import RefreshRepository
from sync.domain import SyncResult
from sync.orchestration.service import SyncOrchestrator
from sync.readers import (
    BudgetCodeReader,
    ClaimReader,
    CostCenterReader,
    DepartmentReader,
    EmployeeReader,
    PayrollReader,
)

ALL_READERS = [
    DepartmentReader(),
    EmployeeReader(),
    CostCenterReader(),
    BudgetCodeReader(),
    ClaimReader(),
    PayrollReader(),
]

STAGE_HANDLERS: dict[RefreshStage, str] = {
    "extract_source": "_extract_source",
    "normalize_ontology": "_normalize_ontology",
    "rebuild_aggregates": "_rebuild_aggregates",
    "detect_anomalies": "_detect_anomalies",
    "generate_insights": "_generate_insights",
    "publish_snapshot": "_publish_snapshot",
}


class RefreshOrchestrator:
    def __init__(
        self,
        app_db: Session,
        source_db: Session,
    ):
        self._app_db = app_db
        self._source_db = source_db
        self._repo = RefreshRepository(app_db)
        self._sync_result: SyncResult | None = None
        self._snapshot_id: str | None = None

    def run(self, job: RefreshJob) -> RefreshJob:
        job.status = "running"
        job.started_at = utcnow()
        self._repo.update_job(job)

        self._sync_result = None
        self._snapshot_id = None

        for stage in STAGE_ORDER:
            job.current_stage = stage
            self._repo.update_job(job)

            try:
                method_name = STAGE_HANDLERS[stage]
                getattr(self, method_name)(job)
            except Exception as exc:
                self._safe_rollback()
                job.status = "failed"
                job.finished_at = utcnow()
                job.error_message = f"{stage}: {exc}"
                self._safe_update_job(job)
                return job

        job.status = "completed"
        job.finished_at = utcnow()
        job.current_stage = None
        self._repo.update_job(job)
        return job

    def _extract_source(self, job: RefreshJob) -> None:
        orchestrator = SyncOrchestrator(
            readers=ALL_READERS,  # type: ignore[arg-type]
            app_db=self._app_db,
            source_db=self._source_db,
        )
        result = orchestrator.run()
        self._sync_result = result

        if result.status == "failed":
            raise RuntimeError(result.error_message or "All source readers failed")

        self._snapshot_id = result.snapshot_id
        job.snapshot_id = result.snapshot_id

    def _normalize_ontology(self, job: RefreshJob) -> None:
        if not self._sync_result:
            raise RuntimeError("No sync result available for normalization")

        source_data = self._collect_source_rows()

        orchestrator = OntologyOrchestrator(self._app_db)
        orchestrator.map_all(
            snapshot_id=job.snapshot_id or "",
            departments=source_data.get("departments", []),
            employees=source_data.get("employees", []),
            cost_centers=source_data.get("cost_centers", []),
            budget_codes=source_data.get("budget_codes", []),
            claims=source_data.get("claims", []),
            payroll=source_data.get("payroll", []),
        )

    def _rebuild_aggregates(self, job: RefreshJob) -> None:
        current_month, previous_month = self._resolve_months()
        service = MonthlyAggregationService(self._app_db)
        service.compute_monthly_spends(
            snapshot_id=job.snapshot_id or "",
            current_month=current_month,
            previous_month=previous_month,
        )

    def _detect_anomalies(self, job: RefreshJob) -> None:
        current_month, previous_month = self._resolve_months()
        anomalies = detect_anomalies(
            db=self._app_db,
            snapshot_id=job.snapshot_id or "",
            current_month=current_month,
            previous_month=previous_month,
        )
        self._detected_anomaly_count = len(anomalies)

    def _generate_insights(self, job: RefreshJob) -> None:
        generate_insight(db=self._app_db)

    def _publish_snapshot(self, job: RefreshJob) -> None:
        snapshot_id = job.snapshot_id
        if not snapshot_id:
            raise RuntimeError("No snapshot to publish")

        self._repo.mark_current_snapshot(
            job_id=job.id,
            snapshot_id=snapshot_id,
        )

    def _collect_source_rows(self) -> dict[str, list]:
        source_data: dict[str, list] = {}
        result = self._sync_result
        if result is None:
            return source_data
        for snap in result.snapshots:
            if snap.status == "completed":
                key = snap.entity_type
                source_data[key] = list(snap.rows) if snap.rows else []
        return source_data

    def _resolve_months(self) -> tuple[str, str]:
        from datetime import datetime

        from ontology.schema import PayrollExpenseModel

        months = (
            self._app_db.query(PayrollExpenseModel.payroll_month)
            .distinct()
            .filter(
                PayrollExpenseModel.snapshot_id == self._snapshot_id,
                PayrollExpenseModel.is_resolved,
            )
            .order_by(PayrollExpenseModel.payroll_month.desc())
            .all()
        )
        if months and len(months) >= 2:
            return months[0][0], months[1][0]
        if months:
            current = months[0][0]
            return current, self._previous_month(current)
        now = datetime.now()
        current = now.strftime("%Y-%m")
        return current, self._previous_month(current)

    @staticmethod
    def _previous_month(month_str: str) -> str:
        year_s, month_s = month_str.split("-")
        year = int(year_s)
        month = int(month_s)
        if month == 1:
            return f"{year - 1}-12"
        return f"{year}-{month - 1:02d}"

    def _safe_rollback(self) -> None:
        try:
            self._app_db.rollback()
        except Exception:
            pass

    def _safe_update_job(self, job: RefreshJob) -> None:
        try:
            self._repo.update_job(job)
        except Exception:
            pass
