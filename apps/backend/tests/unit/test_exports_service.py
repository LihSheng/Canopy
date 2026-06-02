from unittest.mock import MagicMock, patch

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


class TestGetSnapshotId:
    """Cover _get_snapshot_id exception path (payload.py lines 67-70)."""

    def test_get_snapshot_id_exception_returns_none(self):
        from unittest.mock import MagicMock, patch

        from exports.payload import _get_snapshot_id

        with patch("exports.payload.get_snapshot_id_from_aggregates", side_effect=RuntimeError("DB error")):
            result = _get_snapshot_id(MagicMock())
            assert result is None


class TestCollectTrendsFiltered:
    """Cover _collect_trends month filtering (payload.py line 152)."""

    def test_collect_trends_filters_by_allowed_months(self):
        from unittest.mock import MagicMock, patch

        from exports.payload import _collect_trends

        mock_spend_1 = MagicMock()
        mock_spend_1.month = "2026-05"
        mock_spend_1.payroll_total = 1000.0
        mock_spend_1.claims_total = 200.0

        mock_spend_2 = MagicMock()
        mock_spend_2.month = "2026-04"
        mock_spend_2.payroll_total = 900.0
        mock_spend_2.claims_total = 100.0

        with (
            patch("exports.payload.get_all_monthly_spends", return_value=[mock_spend_1, mock_spend_2]),
            patch("exports.payload.get_snapshot_id_from_aggregates", return_value="snap-1"),
            patch("exports.payload.get_distinct_months", return_value=["2026-05"]),
        ):
            trends = _collect_trends(MagicMock(), time_range="this_month")
            assert len(trends) == 1
            assert trends[0].month == "2026-05"
            assert trends[0].total == 1200.0


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


class TestDefaultExportDir:
    """Cover _default_export_dir (service.py lines 20, 27)."""

    def test_with_setting_returns_setting(self):
        """line 20: settings.export_storage_dir is set."""
        with patch("exports.service.settings") as mock_s:
            mock_s.export_storage_dir = "/custom/path"
            from exports.service import _default_export_dir

            assert _default_export_dir() == "/custom/path"

    def test_posix_fallback(self):
        """line 27: fallback on posix when no setting."""
        import pathlib

        with (
            patch("exports.service.os.name", "posix"),
            patch("exports.service.settings") as mock_s,
            patch.object(pathlib.Path, "home", return_value=pathlib.PurePosixPath("/home/testuser")),
        ):
            mock_s.export_storage_dir = None
            from exports.service import _default_export_dir

            result = _default_export_dir()
            assert result == "/home/testuser/.canopy-intelligence/exports"

    def test_windows_fallback_uses_localappdata(self):
        """lines 23-25: Windows (nt) fallback reads LOCALAPPDATA env."""

        with (
            patch("exports.service.os.name", "nt"),
            patch("exports.service.settings") as mock_s,
            patch.dict("exports.service.os.environ", {"LOCALAPPDATA": "C:\\Users\\test\\AppData\\Local"}, clear=True),
        ):
            mock_s.export_storage_dir = None
            from exports.service import _default_export_dir

            result = _default_export_dir()
            assert result == "C:\\Users\\test\\AppData\\Local\\Canopy Intelligence\\exports"

    def test_windows_no_localappdata_falls_back_to_home(self):
        """lines 23-27: Windows with no LOCALAPPDATA falls to posix-style home."""
        import pathlib

        with (
            patch("exports.service.os.name", "nt"),
            patch("exports.service.settings") as mock_s,
            patch.dict("exports.service.os.environ", {}, clear=True),
            patch.object(pathlib.Path, "home", return_value=pathlib.PureWindowsPath("C:\\Users\\test")),
        ):
            mock_s.export_storage_dir = None
            from exports.service import _default_export_dir

            result = _default_export_dir()
            assert result == "C:\\Users\\test\\.canopy-intelligence\\exports"


class TestRunExportEdgeCases:
    """Cover _run_export edge cases (service.py lines 131, 161-166)."""

    @patch("exports.service.session_factory")
    def test_run_export_model_not_found_returns_early(self, mock_factory):
        """line 131: model is None -> early return."""
        from exports.service import _run_export

        mock_db = MagicMock()
        mock_factory.return_value = lambda: mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        # Should not raise
        _run_export("nonexistent-job")

    @patch("exports.service.session_factory")
    def test_run_export_exception_sets_failed_status(self, mock_factory):
        """lines 161-166: exception during export sets failed status."""
        from exports.service import _run_export

        mock_db = MagicMock()
        mock_factory.return_value = lambda: mock_db
        mock_model = MagicMock()
        mock_model.id = "job-1"
        mock_model.status = "running"
        mock_model.snapshot_id = "snap-1"
        mock_model.time_range = "this_month"
        mock_model.include_departments = True
        mock_model.include_anomalies = True
        mock_model.file_path = None
        mock_model.file_size_bytes = None
        mock_model.started_at = None
        mock_model.finished_at = None
        mock_model.error_message = None
        mock_model.preset_name = "executive_summary"
        mock_model.requested_by_user_id = "user-1"
        mock_model.snapshot_timestamp = None
        mock_db.query.return_value.filter.return_value.first.return_value = mock_model

        with patch("exports.service.build_workbook", side_effect=RuntimeError("build failed")):
            # Should not raise
            _run_export("job-1")
