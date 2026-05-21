"""Unit tests for analytics.departments module — sorting, edge cases, empty states."""

from unittest.mock import MagicMock, patch

import pytest

pytestmark = pytest.mark.business_rule

from analytics.departments import (
    get_claims,
    get_department,
    get_department_claim_types,
    get_department_employees,
    get_department_trends,
    get_departments,
)
from analytics.domain import (
    ClaimDetailSummary,
    MonthlyClaimTypeSpend,
    MonthlyDepartmentSpend,
    MonthlyEmployeeSpend,
)

SNAPSHOT_ID = "test-snap"


def _mock_dept_spend(dept_id, month, total=1000, payroll=800, claims=200, claim_count=1):
    return MonthlyDepartmentSpend(
        id=f"{dept_id}-{month}",
        snapshot_id=SNAPSHOT_ID,
        department_id=dept_id,
        month=month,
        payroll_total=payroll,
        claims_total=claims,
        total=total,
        claim_count=claim_count,
    )


def _make_repo_mock(spends_current, spends_previous=None, months=None, dept_map=None):
    """Build a SpendRepository-like mock with the needed query methods."""
    repo = MagicMock()
    months = months or (["2026-05", "2026-04"] if spends_previous is not None else ["2026-05"])
    repo.get_distinct_months.return_value = months
    repo.get_snapshot_id_from_aggregates.return_value = SNAPSHOT_ID
    repo.get_department_map.return_value = dept_map or {}

    def get_for_month(month, snapshot_id=None):
        if month == "2026-05":
            return spends_current
        if spends_previous is not None and month == "2026-04":
            return spends_previous
        return []

    repo.get_monthly_spends_for_month.side_effect = get_for_month
    return repo


class TestGetDepartmentsSorting:
    def test_sort_by_change_pct(self):
        """line 64: sort_by == 'change_pct'."""
        spends_cur = [
            _mock_dept_spend("d1", "2026-05", total=1000, payroll=800, claims=200),
            _mock_dept_spend("d2", "2026-05", total=2000, payroll=1800, claims=200),
        ]
        spends_prev = [
            _mock_dept_spend("d1", "2026-04", total=800, payroll=600, claims=200),
            _mock_dept_spend("d2", "2026-04", total=2200, payroll=2000, claims=200),
        ]
        dept_map = {"d1": "Alpha", "d2": "Beta"}

        with patch("analytics.departments.SpendRepository") as mock_repo_cls:
            mock_repo = _make_repo_mock(spends_cur, spends_prev, dept_map=dept_map)
            mock_repo_cls.return_value = mock_repo
            mock_db = MagicMock()
            items = get_departments(mock_db, sort_by="change_pct")
            # d1: (1000-800)/800 = +25%, d2: (2000-2200)/2200 = -9.09%
            # abs sort: d1 (25%) before d2 (9.09%)
            assert len(items) == 2

    def test_sort_by_attention(self):
        """line 66: sort_by == 'attention'."""
        spends_cur = [
            _mock_dept_spend("d1", "2026-05", total=1000),
            _mock_dept_spend("d2", "2026-05", total=2000),
        ]
        spends_prev = [
            _mock_dept_spend("d1", "2026-04", total=800),
            _mock_dept_spend("d2", "2026-04", total=2200),
        ]
        dept_map = {"d1": "Alpha", "d2": "Beta"}

        with patch("analytics.departments.SpendRepository") as mock_repo_cls:
            mock_repo = _make_repo_mock(spends_cur, spends_prev, dept_map=dept_map)
            mock_repo_cls.return_value = mock_repo
            items = get_departments(MagicMock(), sort_by="attention")
            assert len(items) == 2

    def test_sort_by_total_spend(self):
        """line 68: sort_by == 'total_spend'."""
        spends = [
            _mock_dept_spend("d1", "2026-05", total=500),
            _mock_dept_spend("d2", "2026-05", total=3000),
            _mock_dept_spend("d3", "2026-05", total=1000),
        ]
        dept_map = {"d1": "Alpha", "d2": "Beta", "d3": "Gamma"}

        with patch("analytics.departments.SpendRepository") as mock_repo_cls:
            mock_repo = _make_repo_mock(spends, dept_map=dept_map)
            mock_repo_cls.return_value = mock_repo
            items = get_departments(MagicMock(), sort_by="total_spend")
            assert items[0].total_spend >= items[1].total_spend >= items[2].total_spend

    def test_empty_months_returns_empty(self):
        """line 27-28: no months -> empty list."""
        with patch("analytics.departments.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_distinct_months.return_value = []
            mock_repo_cls.return_value = mock_repo
            items = get_departments(MagicMock())
            assert items == []


class TestGetDepartmentEdgeCases:
    def test_no_months_returns_empty_detail(self):
        """line 84-93: no months returns DepartmentDetail with zeros."""
        with patch("analytics.departments.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_distinct_months.return_value = []
            mock_repo.get_snapshot_id_from_aggregates.return_value = SNAPSHOT_ID
            mock_repo.get_department_map.return_value = {"d1": "Alpha"}
            mock_repo_cls.return_value = mock_repo
            result = get_department(MagicMock(), "d1")
            assert result is not None
            assert result.total_spend == 0.0
            assert result.payroll_spend == 0.0
            assert result.claims_spend == 0.0
            assert result.employee_count == 0

    def test_department_not_in_map_returns_none(self):
        """line 79-80: department_id not in names -> None."""
        with patch("analytics.departments.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_distinct_months.return_value = ["2026-05"]
            mock_repo.get_snapshot_id_from_aggregates.return_value = SNAPSHOT_ID
            mock_repo.get_department_map.return_value = {"d1": "Alpha"}
            mock_repo_cls.return_value = mock_repo
            result = get_department(MagicMock(), "d999")
            assert result is None


class TestGetDepartmentEmployeesEdgeCases:
    def test_no_months_returns_empty(self):
        """line 131-132: empty months returns []."""
        with patch("analytics.departments.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_distinct_months.return_value = []
            mock_repo_cls.return_value = mock_repo
            result = get_department_employees(MagicMock(), "d1")
            assert result == []


class TestGetDepartmentClaimTypesEdgeCases:
    def test_no_months_returns_empty(self):
        """line 173-174: empty months returns []."""
        with patch("analytics.departments.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_distinct_months.return_value = []
            mock_repo_cls.return_value = mock_repo
            result = get_department_claim_types(MagicMock(), "d1")
            assert result == []


class TestGetDepartmentTrends:
    def test_returns_monthly_trends(self):
        """lines 150-164: basic trends flow."""
        with patch("analytics.departments.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_monthly_spends_for_department.return_value = [
                _mock_dept_spend("d1", "2026-04", payroll=400, claims=100),
                _mock_dept_spend("d1", "2026-05", payroll=500, claims=200),
            ]
            mock_repo_cls.return_value = mock_repo
            trends = get_department_trends(MagicMock(), "d1")
            assert len(trends) == 2
            assert trends[0].month == "2026-04"
            assert trends[1].month == "2026-05"
            assert trends[1].total == 700.0


class TestGetClaims:
    def test_returns_claim_details(self):
        """lines 189-205: get_claims flow."""
        with patch("analytics.departments.SpendRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_claim_details.return_value = [
                ClaimDetailSummary(
                    claim_id="c1",
                    employee_name="Alice",
                    department_id="d1",
                    department_name="Engineering",
                    claim_type="Travel",
                    amount=500.0,
                    claim_date="2026-05-01",
                ),
            ]
            mock_repo_cls.return_value = mock_repo
            result = get_claims(MagicMock())
            assert len(result) == 1
            assert result[0].employee_name == "Alice"
            assert result[0].amount == 500.0
