from unittest.mock import MagicMock

from common.errors import SyncError
from sync.orchestration.service import SyncOrchestrator


class _FakeReader:
    def __init__(self, entity_type: str, rows: list | None = None, exc: Exception | None = None):
        self.entity_type = entity_type
        self._rows = rows or []
        self._exc = exc

    def read(self, source_db):
        if self._exc:
            raise self._exc
        return list(self._rows)


class TestSyncOrchestratorRun:
    def test_all_readers_succeed(self):
        app_db = MagicMock()
        source_db = MagicMock()
        readers = [
            _FakeReader("departments", [MagicMock(source_key="D001")]),
            _FakeReader("employees", [MagicMock(source_key="E001")]),
        ]
        orchestrator = SyncOrchestrator(readers, app_db, source_db)
        result = orchestrator.run()

        assert result.status == "completed"
        assert len(result.snapshots) == 2
        assert result.snapshots[0].status == "completed"
        assert result.snapshots[0].row_count == 1
        assert result.error_message is None

    def test_partial_failure(self):
        app_db = MagicMock()
        source_db = MagicMock()
        readers = [
            _FakeReader("departments", [MagicMock(source_key="D001")]),
            _FakeReader("employees", exc=SyncError("table missing")),
        ]
        orchestrator = SyncOrchestrator(readers, app_db, source_db)
        result = orchestrator.run()

        assert result.status == "partial"
        assert len(result.snapshots) == 2
        assert result.snapshots[0].status == "completed"
        assert result.snapshots[1].status == "failed"
        assert result.snapshots[1].error_message is not None
        assert "employees" in (result.error_message or "")

    def test_all_fail(self):
        app_db = MagicMock()
        source_db = MagicMock()
        readers = [
            _FakeReader("departments", exc=SyncError("fail")),
            _FakeReader("employees", exc=SyncError("fail")),
        ]
        orchestrator = SyncOrchestrator(readers, app_db, source_db)
        result = orchestrator.run()

        assert result.status == "failed"
        assert all(s.status == "failed" for s in result.snapshots)

    def test_empty_source_returns_zero_rows(self):
        app_db = MagicMock()
        source_db = MagicMock()
        readers = [_FakeReader("departments", [])]
        orchestrator = SyncOrchestrator(readers, app_db, source_db)
        result = orchestrator.run()

        assert result.status == "completed"
        assert result.snapshots[0].row_count == 0

    def test_persists_snapshots_to_app_db(self):
        app_db = MagicMock()
        source_db = MagicMock()
        readers = [_FakeReader("departments", [MagicMock(source_key="D001")])]
        orchestrator = SyncOrchestrator(readers, app_db, source_db)
        orchestrator.run()

        app_db.add.assert_called()
        app_db.commit.assert_called()
