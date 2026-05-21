import pytest

from exports.payload import _collect_departments, _collect_trends, build_payload


class TestExportServiceBuildPayload:
    def testbuild_payload_uses_dashboard_summary(self, db_session, seed_analytics_data):
        db = seed_analytics_data
        payload = build_payload(db, include_departments=True, include_anomalies=True)

        assert payload.snapshot_id == "test-snapshot-001"
        assert payload.department_count == 6
        assert payload.summary_payroll > 0
        assert payload.summary_claims > 0
        assert payload.period_label == "2026-05"

    def testbuild_payload_includes_departments(self, db_session, seed_analytics_data):
        db = seed_analytics_data
        payload = build_payload(db, include_departments=True, include_anomalies=False)

        assert len(payload.departments) > 0
        assert len(payload.anomalies) == 0
        dept_names = [d.department_name for d in payload.departments]
        assert "Engineering" in dept_names

    def testbuild_payload_includes_anomalies(self, db_session, seed_analytics_data):
        db = seed_analytics_data
        payload = build_payload(db, include_departments=False, include_anomalies=True)

        assert len(payload.departments) == 0

    def testbuild_payload_includes_trends(self, db_session, seed_analytics_data):
        db = seed_analytics_data
        payload = build_payload(db, include_departments=False, include_anomalies=False)

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
        payload = build_payload(db, include_departments=True, include_anomalies=True)
        dashboard = get_dashboard_summary(db)

        assert payload.summary_payroll == dashboard.total_payroll
        assert payload.summary_claims == dashboard.total_claims
        assert payload.department_count == dashboard.department_count
        assert payload.snapshot_id == "test-snapshot-001"


class TestExportServiceFallback:
    """Cover _get_snapshot_context when summary is None (payload.py line 54)."""

    def test_get_snapshot_context_returns_none(self):
        from unittest.mock import MagicMock, patch

        from exports.payload import _get_snapshot_context

        with patch("exports.payload.get_dashboard_summary") as mock_summary:
            mock_summary.return_value = None
            result = _get_snapshot_context(MagicMock())
            assert result is None

    def test_build_payload_without_snapshot_context(self):
        """lines 185-194: snapshot_context is None builds fallback."""
        from unittest.mock import MagicMock, patch

        from exports.payload import build_payload

        with (
            patch("exports.payload._get_snapshot_context", return_value=None),
            patch("exports.payload.get_snapshot_id_from_aggregates", return_value="snap-1"),
            patch("exports.payload._collect_departments", return_value=[]),
            patch("exports.payload._collect_anomalies", return_value=[]),
            patch("exports.payload._collect_trends", return_value=[]),
        ):
            payload = build_payload(MagicMock())
            assert payload.snapshot_id == "snap-1"
            assert payload.summary_payroll == 0.0
            assert payload.period_label == ""


class TestExportServiceGenerateExport:
    def test_generate_export_returns_valid_xlsx(self, db_session, seed_analytics_data):
        from exports.service import generate_export

        db = seed_analytics_data
        data = generate_export(db, include_departments=True, include_anomalies=True)

        assert isinstance(data, bytes)
        assert len(data) > 0
        assert data[:2] == b"PK"


class TestExportPresets:
    """Cover resolve_export_preset edge cases (presets.py line 40)."""

    def test_none_returns_default(self):
        from exports.presets import resolve_export_preset

        preset = resolve_export_preset(None)
        assert preset.key == "executive_summary"

    def test_empty_string_returns_default(self):
        from exports.presets import resolve_export_preset

        preset = resolve_export_preset("")
        assert preset.key == "executive_summary"

    def test_unknown_returns_default(self):
        from exports.presets import resolve_export_preset

        preset = resolve_export_preset("nonexistent_preset")
        assert preset.key == "executive_summary"

    def test_valid_key_resolves(self):
        from exports.presets import resolve_export_preset

        preset = resolve_export_preset("department_spend")
        assert preset.key == "department_spend"

    def test_label_lookup(self):
        from exports.presets import resolve_export_preset

        preset = resolve_export_preset("Department Spend")
        assert preset.key == "department_spend"


class TestExportRepository:
    """Cover ExportRepository.update_job with missing job (repository.py line 48)."""

    def test_update_job_not_found_raises(self):
        from unittest.mock import MagicMock

        from exports.domain import ExportJob
        from exports.repository import ExportRepository

        mock_db = MagicMock()
        mock_db.query.return_value.filter.return_value.first.return_value = None

        repo = ExportRepository(mock_db)
        job = ExportJob(id="nonexistent")
        with pytest.raises(ValueError, match="Export job nonexistent not found"):
            repo.update_job(job)


class TestGetExportJob:
    """Cover get_export_job returning None (service.py line 104)."""

    def test_get_export_job_not_found(self):
        from unittest.mock import MagicMock, patch

        from exports.service import get_export_job

        with patch("exports.service.session_factory") as mock_factory:
            mock_db = MagicMock()
            mock_factory.return_value = lambda: mock_db
            mock_db.query.return_value.filter.return_value.first.return_value = None

            result = get_export_job("nonexistent")
            assert result is None


class TestRerunExport:
    """Cover rerun_export with missing job (service.py line 123)."""

    def test_rerun_nonexistent_export(self):
        from unittest.mock import patch

        from exports.service import rerun_export

        with patch("exports.service.get_export_job") as mock_get:
            mock_get.return_value = None
            result = rerun_export("nonexistent")
            assert result is None
