import pytest

from analytics.domain import DashboardSummaryCache, MonthlyDepartmentSpend
from analytics.repositories.spend import SpendRepository
from analytics.repositories.dashboard_cache import DashboardCacheRepository
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

        repo = SpendRepository(db_session)
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

        repo = SpendRepository(db_session)
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

        repo = SpendRepository(db_session)
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

        cache_repo = DashboardCacheRepository(db_session)
        cache = cache_repo.get_latest_summary_cache()
        assert cache is not None
        assert cache.year == 2026
        assert cache.total_payroll > 0

    def test_save_summary_cache_with_string_created_at(self, db_session, seed_analytics_ontology):
        """Cover line 19: save_summary_cache with a non-empty string created_at."""
        cache_repo = DashboardCacheRepository(db_session)
        cache = DashboardSummaryCache(
            snapshot_id="str-time-snap",
            year=2026,
            month=6,
            total_payroll=1000.0,
            total_claims=200.0,
            department_count=1,
            anomaly_count=0,
            created_at="2026-06-15T10:00:00+00:00",
        )
        model = cache_repo.save_summary_cache(cache)
        assert model.id == "str-time-snap"

    def test_get_summary_cache_for_period(self, db_session, seed_analytics_ontology):
        """Cover lines 54-77: get_summary_cache_for_period."""
        _run_pipeline(db_session)
        cache_repo = DashboardCacheRepository(db_session)
        cache = cache_repo.get_summary_cache_for_period(2026, 5)
        assert cache is not None
        assert cache.year == 2026
        assert cache.month == 5

    def test_get_summary_cache_for_period_not_found(self, db_session):
        """Cover line 66-67: model is None returns None."""
        cache_repo = DashboardCacheRepository(db_session)
        cache = cache_repo.get_summary_cache_for_period(2020, 1)
        assert cache is None

    def test_get_summary_cache_for_snapshot(self, db_session, seed_analytics_ontology):
        """Cover lines 79-99: query by snapshot_id."""
        _run_pipeline(db_session)
        cache_repo = DashboardCacheRepository(db_session)
        cache = cache_repo.get_summary_cache_for_snapshot(SNAPSHOT_ID)
        assert cache is not None
        assert cache.snapshot_id == SNAPSHOT_ID

    def test_get_summary_cache_for_snapshot_not_found(self, db_session):
        """Cover line 88-89: model is None returns None."""
        cache_repo = DashboardCacheRepository(db_session)
        cache = cache_repo.get_summary_cache_for_snapshot("nonexistent")
        assert cache is None

    def test_clear_snapshot_removes_data(self, db_session, seed_analytics_ontology):
        run_aggregation_pipeline(
            db=db_session,
            snapshot_id=SNAPSHOT_ID,
            current_month="2026-05",
            previous_month="2026-04",
        )

        spend_repo = SpendRepository(db_session)
        cache_repo = DashboardCacheRepository(db_session)
        spend_repo.clear_spends_for_snapshot(SNAPSHOT_ID)
        cache_repo.clear_snapshot(SNAPSHOT_ID)

        spends = spend_repo.get_monthly_spends_for_month("2026-05")
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

        repo = SpendRepository(db_session)
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

        repo = SpendRepository(db_session)
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

        repo = SpendRepository(db_session)
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

        repo = SpendRepository(db_session)
        names = repo.get_department_map(SNAPSHOT_ID)
        assert names == {"d1": "Engineering", "d2": "Sales"}

    def test_department_map_without_filter(self, db_session, seed_analytics_ontology):
        repo = SpendRepository(db_session)
        names = repo.get_department_map()
        assert len(names) == 2


def _run_pipeline(db_session):
    """Helper to run the standard pipeline."""
    return run_aggregation_pipeline(
        db=db_session,
        snapshot_id=SNAPSHOT_ID,
        current_month="2026-05",
        previous_month="2026-04",
    )


class TestSpendRepositorySnapshotFilters:
    """Cover snapshot_id filter branches in SpendRepository methods."""

    def test_get_monthly_spends_for_month_with_snapshot(self, db_session, seed_analytics_ontology):
        """line 116-117: snapshot_id filter."""
        _run_pipeline(db_session)
        repo = SpendRepository(db_session)
        results = repo.get_monthly_spends_for_month("2026-05", snapshot_id=SNAPSHOT_ID)
        assert len(results) == 2
        # wrong snapshot returns nothing
        empty = repo.get_monthly_spends_for_month("2026-05", snapshot_id="wrong-snap")
        assert len(empty) == 0

    def test_get_monthly_spends_for_department_with_snapshot(self, db_session, seed_analytics_ontology):
        """line 126-127: snapshot_id filter on department query."""
        _run_pipeline(db_session)
        repo = SpendRepository(db_session)
        results = repo.get_monthly_spends_for_department("d1", snapshot_id=SNAPSHOT_ID)
        assert len(results) > 0
        empty = repo.get_monthly_spends_for_department("d1", snapshot_id="wrong-snap")
        assert len(empty) == 0

    def test_get_employee_spends_for_department_with_snapshot(self, db_session, seed_analytics_ontology):
        """line 171-172: snapshot_id filter on employee query."""
        _run_pipeline(db_session)
        repo = SpendRepository(db_session)
        results = repo.get_employee_spends_for_department("d1", snapshot_id=SNAPSHOT_ID)
        assert len(results) > 0
        empty = repo.get_employee_spends_for_department("d1", snapshot_id="wrong-snap")
        assert len(empty) == 0

    def test_get_claim_type_spends_with_snapshot(self, db_session, seed_analytics_ontology):
        """line 200-201: snapshot_id filter on claim type query."""
        _run_pipeline(db_session)
        repo = SpendRepository(db_session)
        results = repo.get_claim_type_spends(snapshot_id=SNAPSHOT_ID)
        assert len(results) > 0
        empty = repo.get_claim_type_spends(snapshot_id="wrong-snap")
        assert len(empty) == 0

    def test_get_employee_contributions_with_snapshot(self, db_session, seed_analytics_ontology):
        """lines 237-240: snapshot_id filters on employee contributions."""
        _run_pipeline(db_session)
        repo = SpendRepository(db_session)
        results = repo.get_employee_contributions("d1", snapshot_id=SNAPSHOT_ID)
        assert len(results) > 0
        empty = repo.get_employee_contributions("d1", snapshot_id="wrong-snap")
        assert len(empty) == 0

    def test_get_claim_details_with_snapshot(self, db_session, seed_analytics_ontology):
        """lines 273-276: snapshot_id filters on claim details."""
        _run_pipeline(db_session)
        repo = SpendRepository(db_session)
        results = repo.get_claim_details(snapshot_id=SNAPSHOT_ID)
        assert len(results) > 0
        empty = repo.get_claim_details(snapshot_id="wrong-snap")
        assert len(empty) == 0
