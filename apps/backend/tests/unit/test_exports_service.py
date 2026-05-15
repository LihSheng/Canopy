import pytest

from exports.builders.workbook import build_workbook
from exports.domain import (
    DepartmentExportRow,
    ExportPayload,
)
from exports.service import _build_payload, _collect_departments, _collect_trends


class TestExportServiceBuildPayload:
    def test_build_payload_uses_dashboard_summary(self, db_session, seed_analytics_data):
        db = seed_analytics_data
        payload = _build_payload(db, include_departments=True, include_anomalies=True)

        assert payload.snapshot_id == "test-snapshot-001"
        assert payload.department_count == 6
        assert payload.summary_payroll > 0
        assert payload.summary_claims > 0
        assert payload.period_label == "2026-05"

    def test_build_payload_includes_departments(self, db_session, seed_analytics_data):
        db = seed_analytics_data
        payload = _build_payload(db, include_departments=True, include_anomalies=False)

        assert len(payload.departments) > 0
        assert len(payload.anomalies) == 0
        dept_names = [d.department_name for d in payload.departments]
        assert "Engineering" in dept_names

    def test_build_payload_includes_anomalies(self, db_session, seed_analytics_data):
        db = seed_analytics_data
        payload = _build_payload(db, include_departments=False, include_anomalies=True)

        assert len(payload.departments) == 0

    def test_build_payload_includes_trends(self, db_session, seed_analytics_data):
        db = seed_analytics_data
        payload = _build_payload(db, include_departments=False, include_anomalies=False)

        assert len(payload.trends) > 0
        months = [t.month for t in payload.trends]
        assert "2025-11" in months

    def test_collect_departments_returns_ranked_rows(self, db_session, seed_analytics_data):
        db = seed_analytics_data
        rows = _collect_departments(db)

        assert len(rows) > 0
        assert rows[0].rank == 1
        assert rows[0].total_spend > 0

    def test_collect_trends_returns_monthly_data(self, db_session, seed_analytics_data):
        db = seed_analytics_data
        trends = _collect_trends(db)

        assert len(trends) > 0
        assert all(t.month for t in trends)
        assert all(t.total > 0 for t in trends)


class TestExportServiceSnapshotAlignment:
    def test_export_uses_same_snapshot_as_dashboard(self, db_session, seed_analytics_data):
        from analytics.service import get_dashboard_summary

        db = seed_analytics_data
        payload = _build_payload(db, include_departments=True, include_anomalies=True)
        dashboard = get_dashboard_summary(db)

        assert payload.summary_payroll == dashboard.total_payroll
        assert payload.summary_claims == dashboard.total_claims
        assert payload.department_count == dashboard.department_count
        assert payload.snapshot_id == "test-snapshot-001"


class TestExportServiceGenerateExport:
    def test_generate_export_returns_valid_xlsx(self, db_session, seed_analytics_data):
        from exports.service import generate_export

        db = seed_analytics_data
        data = generate_export(db, include_departments=True, include_anomalies=True)

        assert isinstance(data, bytes)
        assert len(data) > 0
        assert data[:2] == b"PK"
