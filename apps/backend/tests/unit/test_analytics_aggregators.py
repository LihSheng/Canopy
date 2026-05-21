import pytest

import uuid

from analytics.aggregators.claims import (
    _extract_month,
    aggregate_claims_by_department,
    aggregate_claims_by_employee,
    aggregate_claims_by_type,
)
from analytics.aggregators.deltas import (
    attach_mom_deltas_to_rankings,
    calculate_mom_deltas,
    rank_departments,
)
from analytics.aggregators.merge import merge_department_spend, merge_employee_spend
from analytics.aggregators.payroll import (
    aggregate_payroll_by_department,
    aggregate_payroll_by_employee,
)
from analytics.domain import DepartmentMoMDelta, MonthlyDepartmentSpend

pytestmark = pytest.mark.business_rule


SNAPSHOT_ID = "snap-1"


# ---------------------------------------------------------------------------
# Payroll aggregation
# ---------------------------------------------------------------------------


class TestPayrollMonthlyAggregation:
    def test_groups_by_department_and_month(self):
        rows = [
            {"employee_id": "e1", "department_id": "d1", "payroll_month": "2026-01", "amount": 5000},
            {"employee_id": "e2", "department_id": "d1", "payroll_month": "2026-01", "amount": 3000},
            {"employee_id": "e3", "department_id": "d2", "payroll_month": "2026-01", "amount": 4000},
            {"employee_id": "e1", "department_id": "d1", "payroll_month": "2026-02", "amount": 5200},
        ]
        results = aggregate_payroll_by_department(SNAPSHOT_ID, rows)

        d1_jan = next(r for r in results if r.department_id == "d1" and r.month == "2026-01")
        assert d1_jan.payroll_total == 8000.0
        assert d1_jan.total == 8000.0

        d2_jan = next(r for r in results if r.department_id == "d2" and r.month == "2026-01")
        assert d2_jan.payroll_total == 4000.0

        d1_feb = next(r for r in results if r.department_id == "d1" and r.month == "2026-02")
        assert d1_feb.payroll_total == 5200.0

    def test_empty_rows_returns_empty_list(self):
        results = aggregate_payroll_by_department(SNAPSHOT_ID, [])
        assert results == []

    def test_unresolved_department_treated_as_string(self):
        rows = [
            {"employee_id": "e1", "department_id": None, "payroll_month": "2026-01", "amount": 1000},
        ]
        results = aggregate_payroll_by_department(SNAPSHOT_ID, rows)
        assert len(results) == 1
        assert results[0].department_id == "__unresolved__"

    def test_all_results_have_snapshot_id(self):
        rows = [
            {"employee_id": "e1", "department_id": "d1", "payroll_month": "2026-01", "amount": 1000},
        ]
        results = aggregate_payroll_by_department(SNAPSHOT_ID, rows)
        assert all(r.snapshot_id == SNAPSHOT_ID for r in results)


class TestPayrollEmployeeAggregation:
    def test_groups_by_employee_department_and_month(self):
        rows = [
            {"employee_id": "e1", "department_id": "d1", "payroll_month": "2026-01", "amount": 5000},
            {"employee_id": "e1", "department_id": "d1", "payroll_month": "2026-01", "amount": 2000},
            {"employee_id": "e2", "department_id": "d1", "payroll_month": "2026-01", "amount": 3000},
        ]
        results = aggregate_payroll_by_employee(SNAPSHOT_ID, rows)
        assert len(results) == 2

        e1 = next(r for r in results if r["employee_id"] == "e1")
        assert e1["payroll_total"] == 7000.0
        assert e1["department_id"] == "d1"
        assert e1["month"] == "2026-01"


# ---------------------------------------------------------------------------
# Claims aggregation
# ---------------------------------------------------------------------------


class TestExtractMonth:
    def test_full_date_extracts_year_month(self):
        assert _extract_month("2026-05-15") == "2026-05"

    def test_short_date_passthrough(self):
        assert _extract_month("2026-05") == "2026-05"

    def test_very_short_date_returns_raw(self):
        assert _extract_month("abc") == "abc"
        assert _extract_month("") == ""

    def test_none_date_returns_empty(self):
        # len(None) isn't valid, but the function receives a str
        assert _extract_month("None") == "None"


class TestClaimsMonthlyAggregation:
    def test_groups_by_department_and_extracted_month(self):
        rows = [
            {"employee_id": "e1", "department_id": "d1", "claim_date": "2026-01-15", "claim_type": "Travel", "amount": 500},
            {"employee_id": "e2", "department_id": "d1", "claim_date": "2026-01-20", "claim_type": "Meals", "amount": 300},
            {"employee_id": "e3", "department_id": "d2", "claim_date": "2026-02-01", "claim_type": "Travel", "amount": 400},
        ]
        results = aggregate_claims_by_department(SNAPSHOT_ID, rows)

        d1_jan = next(r for r in results if r.department_id == "d1" and r.month == "2026-01")
        assert d1_jan.claims_total == 800.0
        assert d1_jan.claim_count == 2

        d2_feb = next(r for r in results if r.department_id == "d2" and r.month == "2026-02")
        assert d2_feb.claims_total == 400.0
        assert d2_feb.claim_count == 1

    def test_empty_rows_returns_empty(self):
        results = aggregate_claims_by_department(SNAPSHOT_ID, [])
        assert results == []


class TestClaimsEmployeeAggregation:
    def test_groups_by_employee_department_and_month(self):
        rows = [
            {"employee_id": "e1", "department_id": "d1", "claim_date": "2026-01-15", "claim_type": "Travel", "amount": 500},
            {"employee_id": "e1", "department_id": "d1", "claim_date": "2026-01-20", "claim_type": "Meals", "amount": 300},
        ]
        results = aggregate_claims_by_employee(SNAPSHOT_ID, rows)
        assert len(results) == 1
        assert results[0]["claims_total"] == 800.0
        assert results[0]["claim_count"] == 2


# ---------------------------------------------------------------------------
# Claim type aggregation
# ---------------------------------------------------------------------------


class TestClaimTypeAggregation:
    def test_groups_by_type_and_department(self):
        rows = [
            {"employee_id": "e1", "department_id": "d1", "claim_date": "2026-01-15", "claim_type": "Travel", "amount": 500},
            {"employee_id": "e2", "department_id": "d2", "claim_date": "2026-01-20", "claim_type": "Travel", "amount": 300},
            {"employee_id": "e3", "department_id": "d1", "claim_date": "2026-01-10", "claim_type": "Meals", "amount": 200},
        ]
        results = aggregate_claims_by_type(SNAPSHOT_ID, rows)
        assert len(results) == 3

        travel_d1 = next(r for r in results if r.claim_type == "Travel" and r.department_id == "d1")
        assert travel_d1.amount == 500.0
        assert travel_d1.claim_count == 1

        travel_d2 = next(r for r in results if r.claim_type == "Travel" and r.department_id == "d2")
        assert travel_d2.amount == 300.0

        meals = next(r for r in results if r.claim_type == "Meals")
        assert meals.amount == 200.0

    def test_filtered_by_department(self):
        rows = [
            {"employee_id": "e1", "department_id": "d1", "claim_date": "2026-01-15", "claim_type": "Travel", "amount": 500},
            {"employee_id": "e2", "department_id": "d2", "claim_date": "2026-01-20", "claim_type": "Travel", "amount": 300},
        ]
        results = aggregate_claims_by_type(SNAPSHOT_ID, rows, department_id="d1")
        assert len(results) == 1
        assert results[0].department_id == "d1"
        assert results[0].amount == 500.0


# ---------------------------------------------------------------------------
# Merge functions
# ---------------------------------------------------------------------------


class TestDepartmentMerge:
    def test_merges_payroll_and_claims_by_dept_month(self):
        payroll = [
            MonthlyDepartmentSpend(id="p1", snapshot_id=SNAPSHOT_ID, department_id="d1", month="2026-01", payroll_total=8000, total=8000),
            MonthlyDepartmentSpend(id="p2", snapshot_id=SNAPSHOT_ID, department_id="d2", month="2026-01", payroll_total=4000, total=4000),
        ]
        claims = [
            MonthlyDepartmentSpend(id="c1", snapshot_id=SNAPSHOT_ID, department_id="d1", month="2026-01", claims_total=800, total=800, claim_count=2),
        ]

        merged = merge_department_spend(SNAPSHOT_ID, payroll, claims)
        assert len(merged) == 2

        d1 = next(r for r in merged if r.department_id == "d1")
        assert d1.payroll_total == 8000.0
        assert d1.claims_total == 800.0
        assert d1.total == 8800.0
        assert d1.claim_count == 2

        d2 = next(r for r in merged if r.department_id == "d2")
        assert d2.payroll_total == 4000.0
        assert d2.claims_total == 0.0


class TestEmployeeMerge:
    def test_merges_payroll_and_claims_by_employee(self):
        payroll_rows = [
            {"employee_id": "e1", "department_id": "d1", "month": "2026-01", "payroll_total": 5000.0},
            {"employee_id": "e2", "department_id": "d1", "month": "2026-01", "payroll_total": 3000.0},
        ]
        claims_rows = [
            {"employee_id": "e1", "department_id": "d1", "month": "2026-01", "claims_total": 500.0, "claim_count": 1},
        ]

        merged = merge_employee_spend(SNAPSHOT_ID, payroll_rows, claims_rows)
        assert len(merged) == 2

        e1 = next(r for r in merged if r.employee_id == "e1")
        assert e1.payroll_total == 5000.0
        assert e1.claims_total == 500.0
        assert e1.total == 5500.0

        e2 = next(r for r in merged if r.employee_id == "e2")
        assert e2.claims_total == 0.0
        assert e2.total == 3000.0


# ---------------------------------------------------------------------------
# MoM delta calculation
# ---------------------------------------------------------------------------


class TestMoMDeltas:
    def test_calculates_change_between_months(self):
        spends = [
            MonthlyDepartmentSpend(id="a", snapshot_id=SNAPSHOT_ID, department_id="d1", month="2026-04", total=1000),
            MonthlyDepartmentSpend(id="b", snapshot_id=SNAPSHOT_ID, department_id="d1", month="2026-05", total=1200),
        ]
        deltas = calculate_mom_deltas(SNAPSHOT_ID, spends, "2026-05", "2026-04")
        assert len(deltas) == 1
        d = deltas[0]
        assert d.department_id == "d1"
        assert d.current_total == 1200.0
        assert d.previous_total == 1000.0
        assert d.total_change == 200.0
        assert d.total_change_pct == 20.0

    def test_new_department_zero_previous(self):
        spends = [
            MonthlyDepartmentSpend(id="a", snapshot_id=SNAPSHOT_ID, department_id="d1", month="2026-05", total=1200),
        ]
        deltas = calculate_mom_deltas(SNAPSHOT_ID, spends, "2026-05", "2026-04")
        d = deltas[0]
        assert d.previous_total == 0.0
        assert d.total_change_pct == 0.0

    def test_department_only_in_previous_month(self):
        spends = [
            MonthlyDepartmentSpend(id="a", snapshot_id=SNAPSHOT_ID, department_id="d1", month="2026-04", total=1000),
        ]
        deltas = calculate_mom_deltas(SNAPSHOT_ID, spends, "2026-05", "2026-04")
        d = deltas[0]
        assert d.current_total == 0.0
        assert d.total_change == -1000.0


# ---------------------------------------------------------------------------
# Department ranking
# ---------------------------------------------------------------------------


class TestDepartmentRanking:
    def test_ranks_by_total_spend_descending(self):
        spends = [
            MonthlyDepartmentSpend(id="a", snapshot_id=SNAPSHOT_ID, department_id="d1", month="2026-05", total=500, payroll_total=400, claims_total=100),
            MonthlyDepartmentSpend(id="b", snapshot_id=SNAPSHOT_ID, department_id="d2", month="2026-05", total=1000, payroll_total=800, claims_total=200),
            MonthlyDepartmentSpend(id="c", snapshot_id=SNAPSHOT_ID, department_id="d3", month="2026-05", total=750, payroll_total=600, claims_total=150),
        ]
        names = {"d1": "Eng", "d2": "Sales", "d3": "Marketing"}
        rankings = rank_departments(spends, "2026-05", names)
        assert len(rankings) == 3
        assert rankings[0].department_id == "d2"
        assert rankings[0].department_name == "Sales"
        assert rankings[0].rank == 1
        assert rankings[0].total_spend == 1000.0

        assert rankings[1].department_id == "d3"
        assert rankings[1].rank == 2

        assert rankings[2].department_id == "d1"
        assert rankings[2].rank == 3

    def test_only_includes_specified_month(self):
        spends = [
            MonthlyDepartmentSpend(id="a", snapshot_id=SNAPSHOT_ID, department_id="d1", month="2026-04", total=500),
            MonthlyDepartmentSpend(id="b", snapshot_id=SNAPSHOT_ID, department_id="d2", month="2026-05", total=1000),
        ]
        rankings = rank_departments(spends, "2026-05")
        assert len(rankings) == 1
        assert rankings[0].department_id == "d2"


# ---------------------------------------------------------------------------
# Attach MoM deltas
# ---------------------------------------------------------------------------


class TestAttachMoMDeltas:
    def test_attaches_change_pct_to_rankings(self):
        rankings = [
            type("Ranking", (), {"department_id": "d1", "change_pct": 0.0})(),
            type("Ranking", (), {"department_id": "d2", "change_pct": 0.0})(),
        ]
        deltas = [
            DepartmentMoMDelta(snapshot_id="", department_id="d1", current_month="", previous_month="", total_change_pct=15.5),
            DepartmentMoMDelta(snapshot_id="", department_id="d2", current_month="", previous_month="", total_change_pct=-3.2),
        ]
        result = attach_mom_deltas_to_rankings(rankings, deltas)
        assert result[0].change_pct == 15.5
        assert result[1].change_pct == -3.2
