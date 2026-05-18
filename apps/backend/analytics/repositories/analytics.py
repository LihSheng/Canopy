"""
AnalyticsRepository is preserved as a backwards-compatible facade.

New code should prefer the focused repositories:
- analytics.repositories.spend.SpendRepository
- analytics.repositories.dashboard_cache.DashboardCacheRepository
"""

from sqlalchemy.orm import Session

from analytics.domain import (
    ClaimDetailSummary,
    DashboardSummaryCache,
    EmployeeContributionSummary,
    MonthlyClaimTypeSpend,
    MonthlyDepartmentSpend,
    MonthlyEmployeeSpend,
)
from analytics.repositories.dashboard_cache import DashboardCacheRepository
from analytics.repositories.spend import SpendRepository
from analytics.schema import (
    DashboardSummaryCacheModel,
    MonthlyClaimTypeSpendModel,
    MonthlyDepartmentSpendModel,
    MonthlyEmployeeSpendModel,
)


class AnalyticsRepository:
    """Backwards-compatible facade over SpendRepository and DashboardCacheRepository."""

    def __init__(self, db: Session):
        self._db = db
        self._spend_repo = SpendRepository(db)
        self._cache_repo = DashboardCacheRepository(db)

    # ---- persistence ----

    def save_department_spends(
        self, spends: list[MonthlyDepartmentSpend]
    ) -> list[MonthlyDepartmentSpendModel]:
        return self._spend_repo.save_department_spends(spends)

    def save_employee_spends(
        self, spends: list[MonthlyEmployeeSpend]
    ) -> list[MonthlyEmployeeSpendModel]:
        return self._spend_repo.save_employee_spends(spends)

    def save_claim_type_spends(
        self, spends: list[MonthlyClaimTypeSpend]
    ) -> list[MonthlyClaimTypeSpendModel]:
        return self._spend_repo.save_claim_type_spends(spends)

    def clear_snapshot(self, snapshot_id: str) -> None:
        self._spend_repo.clear_spends_for_snapshot(snapshot_id)
        self._cache_repo.clear_snapshot(snapshot_id)

    # ---- summary cache ----

    def save_summary_cache(self, cache: DashboardSummaryCache) -> DashboardSummaryCacheModel:
        return self._cache_repo.save_summary_cache(cache)

    def get_latest_summary_cache(self) -> DashboardSummaryCache | None:
        return self._cache_repo.get_latest_summary_cache()

    def get_summary_cache_for_period(
        self, year: int, month: int
    ) -> DashboardSummaryCache | None:
        return self._cache_repo.get_summary_cache_for_period(year, month)

    def get_summary_cache_for_snapshot(
        self, snapshot_id: str
    ) -> DashboardSummaryCache | None:
        return self._cache_repo.get_summary_cache_for_snapshot(snapshot_id)

    # ---- monthly department spends ----

    def get_monthly_spends_for_month(
        self, month: str, snapshot_id: str | None = None
    ) -> list[MonthlyDepartmentSpend]:
        return self._spend_repo.get_monthly_spends_for_month(month, snapshot_id=snapshot_id)

    def get_monthly_spends_for_department(
        self, department_id: str, snapshot_id: str | None = None
    ) -> list[MonthlyDepartmentSpend]:
        return self._spend_repo.get_monthly_spends_for_department(department_id, snapshot_id=snapshot_id)

    def get_all_monthly_spends(
        self, snapshot_id: str | None = None
    ) -> list[MonthlyDepartmentSpend]:
        return self._spend_repo.get_all_monthly_spends(snapshot_id=snapshot_id)

    def get_distinct_months(self, snapshot_id: str | None = None) -> list[str]:
        return self._spend_repo.get_distinct_months(snapshot_id=snapshot_id)

    # ---- monthly employee spends ----

    def get_employee_spends_for_department(
        self, department_id: str, month: str | None = None, snapshot_id: str | None = None
    ) -> list[MonthlyEmployeeSpend]:
        return self._spend_repo.get_employee_spends_for_department(
            department_id, month=month, snapshot_id=snapshot_id
        )

    # ---- claim type spends ----

    def get_claim_type_spends(
        self,
        department_id: str | None = None,
        month: str | None = None,
        snapshot_id: str | None = None,
    ) -> list[MonthlyClaimTypeSpend]:
        return self._spend_repo.get_claim_type_spends(
            department_id=department_id, month=month, snapshot_id=snapshot_id
        )

    # ---- department counts ----

    def get_department_count_for_snapshot(self, snapshot_id: str) -> int:
        return self._spend_repo.get_department_count_for_snapshot(snapshot_id)

    # ---- claim detail joins ----

    def get_employee_contributions(
        self,
        department_id: str,
        month: str | None = None,
        snapshot_id: str | None = None,
    ) -> list[EmployeeContributionSummary]:
        return self._spend_repo.get_employee_contributions(
            department_id, month=month, snapshot_id=snapshot_id
        )

    def get_claim_details(
        self,
        department_id: str | None = None,
        snapshot_id: str | None = None,
    ) -> list[ClaimDetailSummary]:
        return self._spend_repo.get_claim_details(
            department_id=department_id, snapshot_id=snapshot_id
        )

    def get_department_map(self, snapshot_id: str | None = None) -> dict[str, str]:
        return self._spend_repo.get_department_map(snapshot_id=snapshot_id)

    def get_snapshot_id_from_aggregates(self) -> str | None:
        return self._spend_repo.get_snapshot_id_from_aggregates()
