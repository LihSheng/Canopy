"""Monthly aggregation service — coordinating seam for the aggregation pipeline.

Callers (refresh orchestrator, exports) use this service instead of
importing builder.run_aggregation_pipeline directly. Tests inject a
mock or spy on this single seam instead of patching builder internals.
"""

from dataclasses import dataclass

from sqlalchemy.orm import Session

from analytics.domain import DashboardSummaryCache
from analytics.repositories.spend import SpendRepository
from analytics.repositories.dashboard_cache import DashboardCacheRepository
from analytics.services.builder import run_aggregation_pipeline


@dataclass
class AggregationInput:
    snapshot_id: str
    current_month: str
    previous_month: str
    anomaly_count: int = 0


@dataclass
class AggregationResult:
    summary: DashboardSummaryCache


class MonthlyAggregationService:
    """Coordinates the monthly aggregation pipeline behind a single interface.

    Usage::

        service = MonthlyAggregationService(db)
        result = service.compute_monthly_spends(
            snapshot_id="...",
            current_month="2026-05",
            previous_month="2026-04",
        )

    Test injection::

        service = MonthlyAggregationService(db)
        service._run_pipeline = mock.AsyncMock()  # or MagicMock
    """

    def __init__(self, db: Session):
        self._db = db
        self._spend_repo = SpendRepository(db)
        self._cache_repo = DashboardCacheRepository(db)

    def compute_monthly_spends(
        self,
        snapshot_id: str,
        current_month: str,
        previous_month: str,
        anomaly_count: int = 0,
    ) -> DashboardSummaryCache:
        """Execute the full aggregation pipeline and return the summary cache."""
        summary = self._run_pipeline(
            snapshot_id=snapshot_id,
            current_month=current_month,
            previous_month=previous_month,
            anomaly_count=anomaly_count,
        )
        return summary

    def compute(self, input_data: AggregationInput) -> AggregationResult:
        """Convenience wrapper accepting an AggregationInput dataclass."""
        summary = self.compute_monthly_spends(
            snapshot_id=input_data.snapshot_id,
            current_month=input_data.current_month,
            previous_month=input_data.previous_month,
            anomaly_count=input_data.anomaly_count,
        )
        return AggregationResult(summary=summary)

    def _run_pipeline(
        self,
        snapshot_id: str,
        current_month: str,
        previous_month: str,
        anomaly_count: int = 0,
    ) -> DashboardSummaryCache:
        return run_aggregation_pipeline(
            db=self._db,
            snapshot_id=snapshot_id,
            current_month=current_month,
            previous_month=previous_month,
            anomaly_count=anomaly_count,
        )

    @property
    def spend_repo(self) -> SpendRepository:
        return self._spend_repo

    @property
    def cache_repo(self) -> DashboardCacheRepository:
        return self._cache_repo
