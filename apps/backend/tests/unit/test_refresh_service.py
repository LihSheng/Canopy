"""Unit tests for refresh/service.py, refresh/repository.py, and refresh/orchestration/service.py edge cases."""

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from refresh.domain import RefreshJob, DataSnapshot

pytestmark = pytest.mark.unit


class TestRefreshService:
    """Cover refresh/service.py edge cases."""

    @patch("refresh.service.session_factory")
    def test_get_job_not_found_returns_none(self, mock_factory):
        """line 73-74: model is None -> return None."""
        from refresh.service import get_job

        mock_db = MagicMock()
        mock_factory.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = get_job("nonexistent")
        assert result is None

    @patch("refresh.service.session_factory")
    @patch("refresh.service.source_session_factory")
    def test_run_refresh_job_not_found(self, mock_source_factory, mock_factory):
        """line 96-97: job_model is None -> early return."""
        from refresh.service import _run_refresh

        mock_db = MagicMock()
        mock_factory.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None

        source_db = MagicMock()
        mock_source_factory.return_value = source_db

        # Should not raise
        _run_refresh("nonexistent")


class TestRefreshRepositoryEdgeCases:
    """Cover refresh/repository.py edge cases (lines 54-67)."""

    def test_save_data_snapshot_with_string_created_at(self):
        """line 56-57: string created_at parsed."""
        mock_db = MagicMock()
        from refresh.repository import RefreshRepository

        repo = RefreshRepository(mock_db)
        snapshot = DataSnapshot(
            id="snap-1",
            refresh_job_id="job-1",
            status="current",
            created_at="2026-05-15T10:00:00+00:00",
        )
        repo.save_data_snapshot(snapshot)
        assert mock_db.add.called
        assert mock_db.commit.called

    def test_save_data_snapshot_with_empty_string(self):
        """line 57: empty string created_at -> utcnow() fallback."""
        mock_db = MagicMock()
        from refresh.repository import RefreshRepository

        repo = RefreshRepository(mock_db)
        snapshot = DataSnapshot(
            id="snap-2",
            refresh_job_id="job-1",
            status="current",
            created_at="",
        )
        repo.save_data_snapshot(snapshot)
        assert mock_db.add.called

    def test_mark_current_snapshot(self):
        """lines 77-92: mark_current_snapshot archives existing and creates new."""
        mock_db = MagicMock()
        from refresh.repository import RefreshRepository

        existing = MagicMock()
        existing.status = "current"
        mock_db.query.return_value.filter.return_value.all.return_value = [existing]

        repo = RefreshRepository(mock_db)
        repo.mark_current_snapshot("job-1", "snap-1")

        assert existing.status == "archived"
        assert mock_db.add.called
        assert mock_db.commit.called


class TestRefreshOrchestratorEdgeCases:
    """Cover RefreshOrchestrator edge cases."""

    def test_normalize_ontology_no_sync_result(self):
        """line 97-98: no sync result -> RuntimeError."""
        from refresh.orchestration.service import RefreshOrchestrator

        orch = RefreshOrchestrator(app_db=MagicMock(), source_db=MagicMock())
        job = RefreshJob(id="test-job")

        with pytest.raises(RuntimeError, match="No sync result available"):
            orch._normalize_ontology(job)

    def test_publish_snapshot_no_snapshot_id(self):
        """line 137-138: no snapshot_id -> RuntimeError."""
        from refresh.orchestration.service import RefreshOrchestrator

        orch = RefreshOrchestrator(app_db=MagicMock(), source_db=MagicMock())
        job = RefreshJob(id="test-job")

        with pytest.raises(RuntimeError, match="No snapshot to publish"):
            orch._publish_snapshot(job)

    def test_safe_rollback_does_not_raise(self):
        """lines 185-189: _safe_rollback swallows exceptions."""
        from refresh.orchestration.service import RefreshOrchestrator

        app_db = MagicMock()
        app_db.rollback.side_effect = Exception("rollback error")
        orch = RefreshOrchestrator(app_db=app_db, source_db=MagicMock())

        # Should not raise
        orch._safe_rollback()

    def test_safe_update_job_does_not_raise(self):
        """lines 191-195: _safe_update_job swallows exceptions."""
        from refresh.orchestration.service import RefreshOrchestrator

        app_db = MagicMock()
        orch = RefreshOrchestrator(app_db=app_db, source_db=MagicMock())

        # Should not raise
        orch._safe_update_job(MagicMock())

    def test_resolve_months_from_db(self):
        """lines 154-174: _resolve_months queries PayrollExpenseModel."""
        from refresh.orchestration.service import RefreshOrchestrator
        from unittest.mock import patch as mock_patch

        app_db = MagicMock()
        query_result = [("2026-05",), ("2026-04",)]
        app_db.query.return_value.distinct.return_value.filter.return_value.order_by.return_value.all.return_value = query_result

        orch = RefreshOrchestrator(app_db=app_db, source_db=MagicMock())
        orch._snapshot_id = "snap-1"

        current, previous = orch._resolve_months()
        assert current == "2026-05"
        assert previous == "2026-04"

    def test_previous_month_january(self):
        """line 181-182: January -> previous December."""
        from refresh.orchestration.service import RefreshOrchestrator

        result = RefreshOrchestrator._previous_month("2026-01")
        assert result == "2025-12"

    def test_previous_month_march(self):
        """line 183: March -> previous February."""
        from refresh.orchestration.service import RefreshOrchestrator

        result = RefreshOrchestrator._previous_month("2026-03")
        assert result == "2026-02"


class TestRefreshDomain:
    """Cover DataSnapshot created_at handling."""

    def test_data_snapshot_with_datetime_created_at(self):
        now = datetime.now(UTC)
        snap = DataSnapshot(id="s1", refresh_job_id="j1", status="current", created_at=now)
        assert snap.created_at == now
