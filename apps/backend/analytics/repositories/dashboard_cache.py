from datetime import UTC, datetime

from sqlalchemy.orm import Session

from analytics.domain import DashboardSummaryCache
from analytics.schema import DashboardSummaryCacheModel
from common.clock import utcnow


class DashboardCacheRepository:
    """Persistence and queries for dashboard summary cache data."""

    def __init__(self, db: Session):
        self._db = db

    def save_summary_cache(self, cache: DashboardSummaryCache) -> DashboardSummaryCacheModel:
        created_at = cache.created_at
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at) if created_at else utcnow()
        model = DashboardSummaryCacheModel(
            id=cache.snapshot_id,
            snapshot_id=cache.snapshot_id,
            year=cache.year,
            month=cache.month,
            total_payroll=cache.total_payroll,
            total_claims=cache.total_claims,
            department_count=cache.department_count,
            anomaly_count=cache.anomaly_count,
            created_at=created_at,
        )
        self._db.add(model)
        self._db.commit()
        return model

    def get_latest_summary_cache(self) -> DashboardSummaryCache | None:
        model = (
            self._db.query(DashboardSummaryCacheModel)
            .order_by(DashboardSummaryCacheModel.created_at.desc())
            .first()
        )
        if model is None:
            return None
        return DashboardSummaryCache(
            snapshot_id=model.snapshot_id,
            year=model.year,
            month=model.month,
            total_payroll=model.total_payroll,
            total_claims=model.total_claims,
            department_count=model.department_count,
            anomaly_count=model.anomaly_count,
            created_at=model.created_at.isoformat() if model.created_at is not None else "",
        )

    def get_summary_cache_for_period(
        self, year: int, month: int
    ) -> DashboardSummaryCache | None:
        model = (
            self._db.query(DashboardSummaryCacheModel)
            .filter(
                DashboardSummaryCacheModel.year == year,
                DashboardSummaryCacheModel.month == month,
            )
            .order_by(DashboardSummaryCacheModel.created_at.desc())
            .first()
        )
        if model is None:
            return None
        return DashboardSummaryCache(
            snapshot_id=model.snapshot_id,
            year=model.year,
            month=model.month,
            total_payroll=model.total_payroll,
            total_claims=model.total_claims,
            department_count=model.department_count,
            anomaly_count=model.anomaly_count,
            created_at=model.created_at.isoformat() if model.created_at is not None else "",
        )

    def get_summary_cache_for_snapshot(
        self, snapshot_id: str
    ) -> DashboardSummaryCache | None:
        model = (
            self._db.query(DashboardSummaryCacheModel)
            .filter(DashboardSummaryCacheModel.snapshot_id == snapshot_id)
            .order_by(DashboardSummaryCacheModel.created_at.desc())
            .first()
        )
        if model is None:
            return None
        return DashboardSummaryCache(
            snapshot_id=model.snapshot_id,
            year=model.year,
            month=model.month,
            total_payroll=model.total_payroll,
            total_claims=model.total_claims,
            department_count=model.department_count,
            anomaly_count=model.anomaly_count,
            created_at=model.created_at.isoformat() if model.created_at is not None else "",
        )

    def clear_snapshot(self, snapshot_id: str) -> None:
        self._db.query(DashboardSummaryCacheModel).filter(
            DashboardSummaryCacheModel.snapshot_id == snapshot_id
        ).delete()
        self._db.commit()
