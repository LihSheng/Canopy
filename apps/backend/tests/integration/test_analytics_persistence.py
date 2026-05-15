import pytest

from analytics.domain import DashboardSummaryCache, MonthlyDepartmentSpend
from analytics.repositories.analytics import AnalyticsRepository
from analytics.services.builder import run_aggregation_pipeline
from ontology.schema import (
    DepartmentModel,
    EmployeeModel,
    ExpenseClaimModel,
    PayrollExpenseModel,
)

SNAPSHOT_ID = "snap-analytics-test"


@pytest.fixture
def seed_analytics_ontology(db_session):
    departments = [
        DepartmentModel(id="d1", snapshot_id=SNAPSHOT_ID, source_department_key="sk-d1", source_lineage=SNAPSHOT_ID, name="Engineering"),
        DepartmentModel(id="d2", snapshot_id=SNAPSHOT_ID, source_department_key="sk-d2", source_lineage=SNAPSHOT_ID, name="Sales"),
    ]
    db_session.add_all(departments)

    employees = [
        EmployeeModel(id="e1", snapshot_id=SNAPSHOT_ID, source_employee_key="sk-e1", source_lineage=SNAPSHOT_ID, department_id="d1", full_name="Alice", employee_code="A001"),
        EmployeeModel(id="e2", snapshot_id=SNAPSHOT_ID, source_employee_key="sk-e2", source_lineage=SNAPSHOT_ID, department_id="d2", full_name="Bob", employee_code="B001"),
    ]
    db_session.add_all(employees)

    payroll = [
        PayrollExpenseModel(id="p1", snapshot_id=SNAPSHOT_ID, source_payroll_key="spk-1", source_lineage=SNAPSHOT_ID, employee_id="e1", department_id="d1", payroll_month="2026-05", amount=5000, is_resolved=True),
        PayrollExpenseModel(id="p2", snapshot_id=SNAPSHOT_ID, source_payroll_key="spk-2", source_lineage=SNAPSHOT_ID, employee_id="e1", department_id="d1", payroll_month="2026-05", amount=3000, is_resolved=True),
        PayrollExpenseModel(id="p3", snapshot_id=SNAPSHOT_ID, source_payroll_key="spk-3", source_lineage=SNAPSHOT_ID, employee_id="e2", department_id="d2", payroll_month="2026-05", amount=6000, is_resolved=True),
        PayrollExpenseModel(id="p4", snapshot_id=SNAPSHOT_ID, source_payroll_key="spk-4", source_lineage=SNAPSHOT_ID, employee_id="e1", department_id="d1", payroll_month="2026-04", amount=4500, is_resolved=True),
    ]
    db_session.add_all(payroll)

    claims = [
        ExpenseClaimModel(id="c1", snapshot_id=SNAPSHOT_ID, source_claim_key="sck-1", source_lineage=SNAPSHOT_ID, employee_id="e1", department_id="d1", claim_type="Travel", claim_date="2026-05-10", amount=500, is_resolved=True),
        ExpenseClaimModel(id="c2", snapshot_id=SNAPSHOT_ID, source_claim_key="sck-2", source_lineage=SNAPSHOT_ID, employee_id="e2", department_id="d2", claim_type="Meals", claim_date="2026-05-12", amount=200, is_resolved=True),
        ExpenseClaimModel(id="c3", snapshot_id=SNAPSHOT_ID, source_claim_key="sck-3", source_lineage=SNAPSHOT_ID, employee_id="e1", department_id="d1", claim_type="Travel", claim_date="2026-05-15", amount=300, is_resolved=True),
    ]
    db_session.add_all(claims)
    db_session.commit()


class TestAnalyticsPersistence:
    def test_run_aggregation_pipeline_persists_data(self, db_session, seed_analytics_ontology):
        summary = run_aggregation_pipeline(
            db=db_session,
            snapshot_id=SNAPSHOT_ID,
            current_month="2026-05",
            previous_month="2026-04",
            anomaly_count=2,
        )

        assert summary.year == 2026
        assert summary.month == 5
        assert summary.total_payroll == 14000.0  # 5000+3000+6000
        assert summary.total_claims == 1000.0  # 500+200+300
        assert summary.department_count == 2
        assert summary.anomaly_count == 2
        assert summary.created_at != ""

    def test_department_spends_persisted(self, db_session, seed_analytics_ontology):
        run_aggregation_pipeline(
            db=db_session,
            snapshot_id=SNAPSHOT_ID,
            current_month="2026-05",
            previous_month="2026-04",
        )

        repo = AnalyticsRepository(db_session)
        spends = repo.get_monthly_spends_for_month("2026-05")
        assert len(spends) == 2

        d1 = next(s for s in spends if s.department_id == "d1")
        assert d1.payroll_total == 8000.0
        assert d1.claims_total == 800.0
        assert d1.total == 8800.0

        d2 = next(s for s in spends if s.department_id == "d2")
        assert d2.payroll_total == 6000.0
        assert d2.claims_total == 200.0

    def test_employee_spends_persisted(self, db_session, seed_analytics_ontology):
        run_aggregation_pipeline(
            db=db_session,
            snapshot_id=SNAPSHOT_ID,
            current_month="2026-05",
            previous_month="2026-04",
        )

        repo = AnalyticsRepository(db_session)
        spends = repo.get_employee_spends_for_department("d1", month="2026-05")
        assert len(spends) == 1
        assert spends[0].employee_id == "e1"
        assert spends[0].payroll_total == 8000.0
        assert spends[0].claims_total == 800.0

    def test_claim_type_spends_persisted(self, db_session, seed_analytics_ontology):
        run_aggregation_pipeline(
            db=db_session,
            snapshot_id=SNAPSHOT_ID,
            current_month="2026-05",
            previous_month="2026-04",
        )

        repo = AnalyticsRepository(db_session)
        type_spends = repo.get_claim_type_spends(month="2026-05")
        assert len(type_spends) == 2

        travel = next(s for s in type_spends if s.claim_type == "Travel")
        assert travel.amount == 800.0
        assert travel.claim_count == 2

        meals = next(s for s in type_spends if s.claim_type == "Meals")
        assert meals.claim_count == 1

    def test_summary_cache_queryable(self, db_session, seed_analytics_ontology):
        run_aggregation_pipeline(
            db=db_session,
            snapshot_id=SNAPSHOT_ID,
            current_month="2026-05",
            previous_month="2026-04",
        )

        repo = AnalyticsRepository(db_session)
        cache = repo.get_latest_summary_cache()
        assert cache is not None
        assert cache.year == 2026
        assert cache.total_payroll > 0

    def test_clear_snapshot_removes_data(self, db_session, seed_analytics_ontology):
        run_aggregation_pipeline(
            db=db_session,
            snapshot_id=SNAPSHOT_ID,
            current_month="2026-05",
            previous_month="2026-04",
        )

        repo = AnalyticsRepository(db_session)
        repo.clear_snapshot(SNAPSHOT_ID)

        spends = repo.get_monthly_spends_for_month("2026-05")
        assert len(spends) == 0

    def test_pipeline_with_empty_data(self, db_session):
        summary = run_aggregation_pipeline(
            db=db_session,
            snapshot_id="empty-snap",
            current_month="2026-05",
            previous_month="2026-04",
        )

        assert summary.total_payroll == 0.0
        assert summary.total_claims == 0.0

    def test_distinct_months_sorted_descending(self, db_session, seed_analytics_ontology):
        run_aggregation_pipeline(
            db=db_session,
            snapshot_id=SNAPSHOT_ID,
            current_month="2026-05",
            previous_month="2026-04",
        )

        repo = AnalyticsRepository(db_session)
        months = repo.get_distinct_months()
        assert months[0] == "2026-05"
        assert months[1] == "2026-04"

    def test_employee_contributions_with_names(self, db_session, seed_analytics_ontology):
        run_aggregation_pipeline(
            db=db_session,
            snapshot_id=SNAPSHOT_ID,
            current_month="2026-05",
            previous_month="2026-04",
        )

        repo = AnalyticsRepository(db_session)
        contributions = repo.get_employee_contributions("d1", month="2026-05")
        assert len(contributions) == 1
        assert contributions[0].employee_name == "Alice"
        assert contributions[0].department_name == "Engineering"

    def test_claim_details_with_names(self, db_session, seed_analytics_ontology):
        run_aggregation_pipeline(
            db=db_session,
            snapshot_id=SNAPSHOT_ID,
            current_month="2026-05",
            previous_month="2026-04",
        )

        repo = AnalyticsRepository(db_session)
        details = repo.get_claim_details(department_id="d1")
        assert len(details) == 2
        assert all(c.department_name == "Engineering" for c in details)
        assert details[0].employee_name == "Alice"

    def test_department_map_returns_names(self, db_session, seed_analytics_ontology):
        run_aggregation_pipeline(
            db=db_session,
            snapshot_id=SNAPSHOT_ID,
            current_month="2026-05",
            previous_month="2026-04",
        )

        repo = AnalyticsRepository(db_session)
        names = repo.get_department_map(SNAPSHOT_ID)
        assert names == {"d1": "Engineering", "d2": "Sales"}

    def test_department_map_without_filter(self, db_session, seed_analytics_ontology):
        repo = AnalyticsRepository(db_session)
        names = repo.get_department_map()
        assert len(names) == 2
