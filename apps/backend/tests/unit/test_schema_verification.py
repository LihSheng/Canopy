import pytest

pytestmark = pytest.mark.api_schema

from sqlalchemy import inspect

from common.database import Base


EXPECTED_TABLES = {
    "users",
    "source_snapshots",
    "source_snapshot_rows",
    "departments",
    "employees",
    "cost_centers",
    "budget_codes",
    "expense_claims",
    "payroll_expenses",
    "unresolved_mapping_issues",
    "analytics_monthly_department_spend",
    "analytics_monthly_employee_spend",
    "analytics_monthly_claim_type_spend",
    "analytics_dashboard_summary_cache",
    "detected_anomalies",
    "generated_insights",
    "refresh_jobs",
    "data_snapshots",
    "export_jobs",
    "v3_uploads",
    "v3_mapping_decisions",
    "v3_cleaning_pipelines",
    "v3_cleaning_steps",
    "v3_template_families",
    "v3_template_versions",
}


def _column_type(engine, table, column):
    inspector = inspect(engine)
    cols = {c["name"]: c for c in inspector.get_columns(table)}
    return cols[column]["type"]


class TestSchemaVerification:
    def test_all_expected_tables_exist(self, engine):
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        missing = EXPECTED_TABLES - tables
        assert not missing, f"Missing tables: {missing}"

    def test_no_unexpected_tables(self, engine):
        inspector = inspect(engine)
        tables = set(inspector.get_table_names())
        extra = tables - EXPECTED_TABLES
        assert not extra, f"Unexpected tables: {extra}"

    def test_users_columns(self, engine):
        inspector = inspect(engine)
        cols = {c["name"]: c for c in inspector.get_columns("users")}
        assert cols["id"]["type"].__class__.__name__ == "VARCHAR"
        assert cols["email"]["nullable"] is False
        assert cols["is_active"]["type"].__class__.__name__ == "BOOLEAN"

    def test_expense_claims_has_numeric_amount(self, engine):
        t = _column_type(engine, "expense_claims", "amount")
        assert t.__class__.__name__ == "NUMERIC", f"Expected NUMERIC, got {t.__class__.__name__}"

    def test_payroll_expenses_has_numeric_amount(self, engine):
        t = _column_type(engine, "payroll_expenses", "amount")
        assert t.__class__.__name__ == "NUMERIC", f"Expected NUMERIC, got {t.__class__.__name__}"

    def test_analytics_monthly_department_spend_has_numeric_totals(self, engine):
        for col_name in ("payroll_total", "claims_total", "total"):
            t = _column_type(engine, "analytics_monthly_department_spend", col_name)
            assert t.__class__.__name__ == "NUMERIC", f"{col_name} expected NUMERIC, got {t.__class__.__name__}"

    def test_analytics_monthly_employee_spend_has_numeric_totals(self, engine):
        for col_name in ("payroll_total", "claims_total", "total"):
            t = _column_type(engine, "analytics_monthly_employee_spend", col_name)
            assert t.__class__.__name__ == "NUMERIC", f"{col_name} expected NUMERIC, got {t.__class__.__name__}"

    def test_generated_insights_has_datetime_generated_at(self, engine):
        t = _column_type(engine, "generated_insights", "generated_at")
        assert t.__class__.__name__ == "DATETIME", f"Expected DATETIME, got {t.__class__.__name__}"

    def test_data_snapshots_has_datetime_created_at(self, engine):
        t = _column_type(engine, "data_snapshots", "created_at")
        assert t.__class__.__name__ == "DATETIME", f"Expected DATETIME, got {t.__class__.__name__}"

    def test_detected_anomalies_has_numeric_values(self, engine):
        for col_name in ("baseline_value", "observed_value", "delta_value"):
            t = _column_type(engine, "detected_anomalies", col_name)
            assert t.__class__.__name__ == "NUMERIC", f"{col_name} expected NUMERIC, got {t.__class__.__name__}"

    def test_indexes_exist_for_snapshot_lookups(self, engine):
        inspector = inspect(engine)
        indexes_by_table = {}
        for table_name in EXPECTED_TABLES:
            indexes = inspector.get_indexes(table_name)
            indexes_by_table[table_name] = {ix["name"] for ix in indexes}

        assert "ix_departments_snapshot_src" in indexes_by_table["departments"]
        assert "ix_employees_snapshot_dept" in indexes_by_table["employees"]
        assert "ix_analytics_dept_spend_snapshot_month" in indexes_by_table["analytics_monthly_department_spend"]
        assert "ix_analytics_dept_spend_snapshot_dept_month" in indexes_by_table["analytics_monthly_department_spend"]
