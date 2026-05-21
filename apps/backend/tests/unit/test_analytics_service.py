"""Unit tests for analytics.service module — edge cases and filter branches."""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.business_rule

from analytics.service import (
    get_claim_type_breakdown,
    get_dashboard_summary,
    get_monthly_trends,
    get_summary_cache_for_snapshot,
    get_top_departments,
)
from analytics.domain import (
    DashboardSummaryCache,
    MonthlyClaimTypeSpend,
    MonthlyDepartmentSpend,
)

SNAPSHOT_ID = "test-snap"


def _mock_spend(dept_id, month, total=1000, payroll=800, claims=200):
    return MonthlyDepartmentSpend(
        id=f"{dept_id}-{month}",
        snapshot_id=SNAPSHOT_ID,
        department_id=dept_id,
        month=month,
        payroll_total=payroll,
        claims_total=claims,
        total=total,
        claim_count=1,
    )


class TestGetDashboardSummary:
    def test_no_cache_returns_default(self):
        """line 26-37: no cache returns default with current date."""
        with patch("analytics.service.DashboardCacheRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_latest_summary_cache.return_value = None
            mock_repo_cls.return_value = mock_repo
            result = get_dashboard_summary(MagicMock())
            assert result.total_payroll == 0.0
            assert result.total_claims == 0.0
            assert result.department_count == 0
            assert result.anomaly_count == 0


class TestGetMonthlyTrends:
    def test_filter_by_year_and_month(self):
        """lines 78-80: filter trends by year/month."""
        with patch("analytics.service.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_all_monthly_spends.return_value = [
                _mock_spend("d1", "2026-04"),
                _mock_spend("d1", "2026-05"),
                _mock_spend("d1", "2026-06"),
            ]
            mock_repo_cls.return_value = mock_repo
            result = get_monthly_trends(MagicMock(), year=2026, month=5)
            assert len(result) == 1
            assert result[0].month == "2026-05"

    def test_no_filter_returns_all(self):
        """no year/month filter returns all months."""
        with patch("analytics.service.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_all_monthly_spends.return_value = [
                _mock_spend("d1", "2026-04", payroll=400, claims=100),
                _mock_spend("d1", "2026-05", payroll=500, claims=200),
            ]
            mock_repo_cls.return_value = mock_repo
            result = get_monthly_trends(MagicMock())
            assert len(result) == 2
            # 2026-04: 400+100 = 500
            # 2026-05: 500+200 = 700
            assert result[0].total == 500.0
            assert result[1].total == 700.0


class TestGetTopDepartments:
    def test_no_months_returns_empty(self):
        """line 89-90: no months -> empty list."""
        with patch("analytics.service.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_distinct_months.return_value = []
            mock_repo_cls.return_value = mock_repo
            result = get_top_departments(MagicMock())
            assert result == []


class TestGetClaimTypeBreakdown:
    def test_no_months_returns_empty(self):
        """line 128-129: no months -> empty list."""
        with patch("analytics.service.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_distinct_months.return_value = []
            mock_repo_cls.return_value = mock_repo
            result = get_claim_type_breakdown(MagicMock())
            assert result == []

    def test_with_data_returns_sorted(self):
        """lines 131-150: proper sorting and aggregation."""
        with patch("analytics.service.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_distinct_months.return_value = ["2026-05"]
            mock_repo.get_claim_type_spends.return_value = [
                MonthlyClaimTypeSpend(
                    id="t1", snapshot_id=SNAPSHOT_ID, department_id="d1",
                    claim_type="Travel", month="2026-05", amount=500.0, claim_count=2,
                ),
                MonthlyClaimTypeSpend(
                    id="t2", snapshot_id=SNAPSHOT_ID, department_id="d2",
                    claim_type="Meals", month="2026-05", amount=300.0, claim_count=1,
                ),
            ]
            mock_repo_cls.return_value = mock_repo
            result = get_claim_type_breakdown(MagicMock())
            assert len(result) == 2
            assert result[0].type == "Travel"
            assert result[0].amount == 500.0


class TestGetSummaryCacheForSnapshot:
    def test_no_cache_returns_none(self):
        """line 196-197: cache is None returns None."""
        with patch("analytics.service.DashboardCacheRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_summary_cache_for_snapshot.return_value = None
            mock_repo_cls.return_value = mock_repo
            result = get_summary_cache_for_snapshot(MagicMock(), "nonexistent")
            assert result is None
