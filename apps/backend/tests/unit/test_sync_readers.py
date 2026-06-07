import asyncio
from datetime import datetime

import pytest

from sync.readers._source_models import (
    SourceBase,
    SourceBudgetCodeRow,
    SourceClaimRow,
    SourceCostCenterRow,
    SourceDepartmentRow,
    SourceEmployeeRow,
    SourcePayrollRow,
)
from sync.readers.budget_codes import BudgetCodeReader
from sync.readers.claims import ClaimReader
from sync.readers.cost_centers import CostCenterReader
from sync.readers.departments import DepartmentReader
from sync.readers.employees import EmployeeReader
from sync.readers.payroll import PayrollReader
from tests.unit.postgres_test_db import make_postgres_session

pytestmark = pytest.mark.business_rule


def _source_db_with_rows(engine, *row_lists):
    SourceBase.metadata.drop_all(bind=engine)
    SourceBase.metadata.create_all(bind=engine)
    from sqlalchemy.orm import Session

    with Session(engine) as session:
        for rows in row_lists:
            session.add_all(rows)
        session.commit()
    return engine


class TestDepartmentReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourceDepartmentRow(source_key="D001", name="Engineering"),
                SourceDepartmentRow(source_key="D002", name="Marketing"),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = DepartmentReader()
            result = reader.read(source_db)

        assert len(result) == 2
        assert result[0].source_key == "D001"
        assert result[0].name == "Engineering"
        assert result[0].parent_key is None
        assert result[0].status == "active"

    def test_empty_table_returns_empty_list(self, source_engine):
        engine = _source_db_with_rows(source_engine)
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = DepartmentReader()
            result = reader.read(source_db)

        assert result == []

    def test_entity_type(self):
        assert DepartmentReader().entity_type == "departments"


class TestEmployeeReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourceEmployeeRow(
                    source_key="E001",
                    full_name="Alice Tan",
                    department_key="D001",
                    cost_center_key="CC01",
                ),
                SourceEmployeeRow(
                    source_key="E002",
                    full_name="Bob Lim",
                    department_key="D002",
                ),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = EmployeeReader()
            result = reader.read(source_db)

        assert len(result) == 2
        assert result[0].source_key == "E001"
        assert result[0].cost_center_key == "CC01"
        assert result[1].cost_center_key is None


class TestClaimReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourceClaimRow(
                    source_key="C001",
                    employee_key="E001",
                    department_key="D001",
                    amount=150.0,
                    currency="MYR",
                    claim_type="travel",
                    submitted_at="2025-01-15T10:00:00",
                    status="approved",
                ),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = ClaimReader()
            result = reader.read(source_db)

        assert len(result) == 1
        assert result[0].amount == 150.0
        assert result[0].claim_type == "travel"
        assert isinstance(result[0].submitted_at, datetime)

    def test_empty_table(self, source_engine):
        engine = _source_db_with_rows(source_engine)
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = ClaimReader()
            result = reader.read(source_db)

        assert result == []


class TestPayrollReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourcePayrollRow(
                    source_key="P001",
                    employee_key="E001",
                    department_key="D001",
                    amount=5000.0,
                    currency="MYR",
                    period_start="2025-01",
                    period_end="2025-01",
                ),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = PayrollReader()
            result = reader.read(source_db)

        assert len(result) == 1
        assert result[0].amount == 5000.0
        assert result[0].period_start == "2025-01"


class TestCostCenterReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourceCostCenterRow(source_key="CC001", name="R&D", department_key="D001"),
                SourceCostCenterRow(source_key="CC002", name="Admin"),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = CostCenterReader()
            result = reader.read(source_db)

        assert len(result) == 2
        assert result[0].name == "R&D"
        assert result[1].department_key is None


class TestBudgetCodeReader:
    def test_reads_all_rows(self, source_engine):
        engine = _source_db_with_rows(
            source_engine,
            [
                SourceBudgetCodeRow(source_key="B001", name="Opex-IT", department_key="D001"),
            ],
        )
        from sqlalchemy.orm import Session

        with Session(engine) as source_db:
            reader = BudgetCodeReader()
            result = reader.read(source_db)

        assert len(result) == 1
        assert result[0].name == "Opex-IT"


class TestSourceDatabaseManager:
    """Cover _SourceDatabaseManager lazy init and set/reset (source_db.py lines 15-43, 52-65)."""

    def test_source_engine_lazy_init(self):
        """line 23-26: engine created on first access."""
        from sync.source_db import _SourceDatabaseManager

        mgr = _SourceDatabaseManager()
        eng = mgr.source_engine()
        assert eng is not None
        # second call returns cached
        assert mgr.source_engine() is eng

    def test_source_session_factory_lazy_init(self):
        """line 28-33: session factory created on first access."""
        from sync.source_db import _SourceDatabaseManager

        mgr = _SourceDatabaseManager()
        factory = mgr.source_session_factory()
        assert factory is not None

    def test_set_source_engine(self):
        """lines 35-39: set_source_engine replaces engine."""
        from sync.source_db import _SourceDatabaseManager

        mgr = _SourceDatabaseManager()
        handle = make_postgres_session(())
        try:
            mgr.set_source_engine(handle.engine)
            assert mgr.source_engine() is handle.engine
        finally:
            handle.close()

    def test_reset_source_engine(self):
        """lines 41-43: reset clears cache."""
        from sync.source_db import _SourceDatabaseManager

        mgr = _SourceDatabaseManager()
        _ = mgr.source_engine()  # trigger lazy init
        mgr.reset_source_engine()
        # After reset, a new call creates new engine
        eng2 = mgr.source_engine()
        assert eng2 is not None

    def test_public_source_engine_function(self):
        """line 52-53: source_engine() public function."""
        from sync.source_db import source_engine

        e = source_engine()
        assert e is not None

    def test_public_source_session_factory(self):
        """line 56-57: source_session_factory() public function."""
        from sync.source_db import source_session_factory

        f = source_session_factory()
        assert f is not None

    def test_public_set_source_engine(self):
        """line 60-61: set_source_engine() public function."""
        from sync.source_db import set_source_engine

        handle = make_postgres_session(())
        try:
            set_source_engine(handle.engine)
        finally:
            handle.close()

    def test_public_reset_source_engine(self):
        """line 64-65: reset_source_engine() public function."""
        from sync.source_db import reset_source_engine

        reset_source_engine()


class TestBuildSourceEngine:
    """Cover _build_source_engine edge cases (source_db.py line 20)."""

    def test_memory_url_uses_static_pool(self):
        """line 20: SQLite :memory: URL uses StaticPool."""
        from sqlalchemy.pool import StaticPool

        from common.config import settings
        from sync.source_db import _SourceDatabaseManager

        original_url = settings.source_database_url
        try:
            settings.source_database_url = "sqlite:///:memory:"
            mgr = _SourceDatabaseManager()
            # Reset internal state so _build_source_engine is called fresh
            mgr._source_engine = None
            eng = mgr.source_engine()
            assert isinstance(eng.pool, StaticPool)
        finally:
            settings.source_database_url = original_url


@pytest.mark.asyncio
class TestMysqlCdcReader:
    """Cover mysql_cdc_reader.py basic methods."""

    async def test_init_sets_attributes(self):
        """lines 21-24: __init__ sets attributes."""
        from sync.readers.mysql_cdc_reader import MysqlCdcReader

        reader = MysqlCdcReader({"host": "localhost"}, "ds-1", "test_table")
        assert reader.config == {"host": "localhost"}
        assert reader.dataset_id == "ds-1"
        assert reader.table_name == "test_table"
        assert reader.running is False

    async def test_stop_sets_running_false(self):
        """line 156: stop sets running to False."""
        from sync.readers.mysql_cdc_reader import MysqlCdcReader

        reader = MysqlCdcReader({}, "ds-1", "tbl")
        reader.running = True
        reader.stop()
        assert reader.running is False

    async def test_import_error_propagates(self):
        """When mysql-replication is not installed, ImportError propagates (no simulation)."""
        from pathlib import Path
        from unittest.mock import MagicMock

        from sync.readers.mysql_cdc_reader import MysqlCdcReader

        reader = MysqlCdcReader({}, "ds-1", "tbl")
        mock_on_event = MagicMock()

        # mysql-replication is not installed, so start_streaming will hit the import path
        with pytest.raises(ImportError):
            await reader.start_streaming(Path("/tmp/events.jsonl"), mock_on_event)

        # on_event should never have been called (no simulation)
        assert not mock_on_event.called

    # ------------------------------------------------------------------
    # binlog streaming path
    # ------------------------------------------------------------------

    async def test_start_streaming_binlog_success_import(self):
        """Cover lines 44-46, 54-107: mysql-replication import succeeds, binlog streaming loop runs."""
        import sys
        import tempfile
        from pathlib import Path
        from unittest.mock import MagicMock, patch

        # Create stub classes so isinstance() works — MagicMock instances
        # are not types and would raise TypeError inside start_streaming.
        class _StubWriteRowsEvent:
            pass

        class _StubUpdateRowsEvent:
            pass

        class _StubDeleteRowsEvent:
            pass

        # Build a fake mysqlreplication module so the dynamic import succeeds
        fake_mysqlreplication = MagicMock()
        fake_row_event = MagicMock()
        fake_mysqlreplication.row_event = fake_row_event

        mock_binlog_stream = MagicMock()
        mock_binlog_stream.log_file = "mysql-bin.000001"
        mock_binlog_stream.log_pos = 1234
        mock_binlog_stream.close = MagicMock()

        fake_mysqlreplication.BinLogStreamReader = MagicMock(return_value=mock_binlog_stream)
        fake_row_event.WriteRowsEvent = _StubWriteRowsEvent
        fake_row_event.UpdateRowsEvent = _StubUpdateRowsEvent
        fake_row_event.DeleteRowsEvent = _StubDeleteRowsEvent

        # Simulate one WriteRows event then stop
        event_sent = [False]

        def mock_fetchone():
            if not event_sent[0]:
                event_sent[0] = True
                mock_event = _StubWriteRowsEvent()
                mock_event.rows = [{"values": {"id": 1, "name": "test"}}]
                return mock_event
            return None

        mock_binlog_stream.fetchone = mock_fetchone

        mock_on_event = MagicMock()

        patched_modules = {
            "mysqlreplication": fake_mysqlreplication,
            "mysqlreplication.row_event": fake_row_event,
        }
        with patch.dict(sys.modules, patched_modules):
            from sync.readers.mysql_cdc_reader import MysqlCdcReader

            reader = MysqlCdcReader(
                {"host": "myhost", "port": 3307, "database": "mydb", "username": "myuser", "password": "mypass"},
                "ds-1",
                "tbl",
            )

            # Stop the loop after first event
            original_fetchone = mock_binlog_stream.fetchone

            def fetchone_then_stop():
                reader.running = False
                return original_fetchone()

            mock_binlog_stream.fetchone = fetchone_then_stop

            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "events.jsonl"
                await reader.start_streaming(path, mock_on_event)

                assert "mysql-bin.000001" in path.read_text(encoding="utf-8")
                assert mock_on_event.called

    async def test_start_streaming_binlog_update_event(self):
        """Cover lines 85-98: UpdateRowsEvent and DeleteRowsEvent branches in binlog loop."""
        import json
        import sys
        import tempfile
        from pathlib import Path
        from unittest.mock import MagicMock, patch

        # Create stub classes so isinstance() works — MagicMock instances
        # are not types and would raise TypeError inside start_streaming.
        class _StubWriteRowsEvent:
            pass

        class _StubUpdateRowsEvent:
            pass

        class _StubDeleteRowsEvent:
            pass

        fake_mysqlreplication = MagicMock()
        fake_row_event = MagicMock()
        fake_mysqlreplication.row_event = fake_row_event
        fake_mysqlreplication.BinLogStreamReader = MagicMock()
        fake_row_event.WriteRowsEvent = _StubWriteRowsEvent
        fake_row_event.UpdateRowsEvent = _StubUpdateRowsEvent
        fake_row_event.DeleteRowsEvent = _StubDeleteRowsEvent

        mock_binlog_stream = MagicMock()
        mock_binlog_stream.log_file = "mysql-bin.000002"
        mock_binlog_stream.log_pos = 5678
        mock_binlog_stream.close = MagicMock()

        # Events to return: Update, then Delete.
        # UpdateRowsEvent rows in mysql-replication have "before_values"
        # and "after_values"; DeleteRowsEvent rows have only "values".
        # The reader accesses row["values"] unconditionally at line 83
        # before the isinstance branch, so update-event rows must also
        # carry a "values" key.
        update_event_data = [
            {
                "type": "update",
                "rows": [{"values": {"id": 2, "name": "old"}, "after_values": {"id": 2, "name": "updated"}}],
            },
            {"type": "delete", "rows": [{"values": {"id": 3, "name": "deleted"}}]},
        ]
        event_idx = [0]

        def mock_fetchone():
            idx = event_idx[0]
            if idx >= len(update_event_data):
                return None
            event_idx[0] += 1
            entry = update_event_data[idx]
            # Return the correct stub type so isinstance branches work.
            if entry["type"] == "update":
                mock_event = _StubUpdateRowsEvent()
            else:
                mock_event = _StubDeleteRowsEvent()
            mock_event.rows = entry["rows"]
            return mock_event

        mock_binlog_stream.fetchone = mock_fetchone
        fake_mysqlreplication.BinLogStreamReader.return_value = mock_binlog_stream

        mock_on_event = MagicMock()

        patched_modules = {
            "mysqlreplication": fake_mysqlreplication,
            "mysqlreplication.row_event": fake_row_event,
        }
        with patch.dict(sys.modules, patched_modules):
            from sync.readers.mysql_cdc_reader import MysqlCdcReader

            reader = MysqlCdcReader(
                {"host": "myhost", "port": 3307, "database": "mydb", "username": "myuser", "password": "mypass"},
                "ds-1",
                "tbl",
            )
            reader.running = True

            def patched_fetchone():
                if event_idx[0] >= len(update_event_data):
                    reader.running = False
                    return None
                return mock_fetchone()

            mock_binlog_stream.fetchone = patched_fetchone

            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "events.jsonl"
                await reader.start_streaming(path, mock_on_event)

                # Assertions must be inside the TemporaryDirectory context
                # — path is deleted once the context exits.
                lines = path.read_text(encoding="utf-8").strip().split("\n")
                assert len(lines) == 2
                assert json.loads(lines[0])["op"] == "UPDATE"
                assert json.loads(lines[1])["op"] == "DELETE"
                assert mock_on_event.call_count == 2


@pytest.mark.asyncio
class TestPostgresCdcReader:
    """Cover pg_cdc_reader.py basic methods."""

    async def test_init_sets_attributes(self):
        """lines 23-26: __init__ sets attributes."""
        from sync.readers.pg_cdc_reader import PostgresCdcReader

        reader = PostgresCdcReader({"host": "localhost"}, "ds-1", "test_table")
        assert reader.config == {"host": "localhost"}
        assert reader.dataset_id == "ds-1"
        assert reader.table_name == "test_table"
        assert reader.running is False

    async def test_stop_sets_running_false(self):
        """line 156: stop sets running to False."""
        from sync.readers.pg_cdc_reader import PostgresCdcReader

        reader = PostgresCdcReader({}, "ds-1", "tbl")
        reader.running = True
        reader.stop()
        assert reader.running is False

    async def test_connection_failure_propagates(self):
        """CDC connection failure propagates out of start_streaming (no simulation fallback)."""
        from pathlib import Path
        from unittest.mock import AsyncMock, MagicMock, patch

        from sync.readers.pg_cdc_reader import PostgresCdcReader

        reader = PostgresCdcReader(
            {"host": "realdb", "port": 5432, "database": "proddb", "username": "usr", "password": "pwd"},
            "ds-1",
            "tbl",
        )

        mock_on_event = MagicMock()
        with patch(
            "psycopg.AsyncConnection.connect",
            AsyncMock(side_effect=ConnectionError("replication slot unavailable")),
        ):
            with pytest.raises(ConnectionError, match="replication slot unavailable"):
                await reader.start_streaming(Path("/tmp/events.jsonl"), mock_on_event)

        # on_event should never have been called (no simulation)
        assert not mock_on_event.called

    # ------------------------------------------------------------------
    # ------ replication streaming path ------
    # ------------------------------------------------------------------

    async def test_start_streaming_replication_success(self):
        """Cover lines 54-103: full replication path with publication/slot creation and message streaming."""
        import tempfile
        from pathlib import Path
        from unittest.mock import AsyncMock, MagicMock, patch

        # Mock cursor for check connection (publication/slot checks)
        mock_check_cursor = AsyncMock()
        mock_check_cursor.fetchone = AsyncMock(return_value=None)  # trigger creation branches
        mock_check_cursor.execute = AsyncMock()

        mock_check_conn = AsyncMock()
        mock_check_conn.cursor = MagicMock(return_value=mock_check_cursor)
        mock_check_conn.__aenter__ = AsyncMock(return_value=mock_check_conn)
        mock_check_conn.__aexit__ = AsyncMock(return_value=None)

        # Mock replication connection
        mock_msg = MagicMock()
        mock_msg.payload = b"table public.test: INSERT: id[integer]:1 name[character varying]:'Alice'"
        mock_msg.wal_start = 42

        call_count = [0]

        reader_ref = [None]  # capture reader to stop loop from receive

        async def mock_receive():
            call_count[0] += 1
            if call_count[0] == 1:
                return mock_msg
            # Stop after first message delivered
            if reader_ref[0]:
                reader_ref[0].running = False
            return None

        mock_repl_conn = AsyncMock()
        mock_repl_conn.receive = mock_receive
        mock_repl_conn.send_feedback = MagicMock()
        mock_repl_cursor = AsyncMock()
        mock_repl_cursor.execute = AsyncMock()
        mock_repl_conn.cursor = MagicMock(return_value=mock_repl_cursor)
        mock_repl_conn.__aenter__ = AsyncMock(return_value=mock_repl_conn)
        mock_repl_conn.__aexit__ = AsyncMock(return_value=None)

        connect_calls = [mock_check_conn, mock_repl_conn]
        call_idx = [0]

        async def mock_connect_fn(*args, **kwargs):
            idx = call_idx[0]
            call_idx[0] += 1
            return connect_calls[idx]

        mock_on_event = MagicMock()

        with patch("sync.readers.pg_cdc_reader.psycopg.AsyncConnection.connect", mock_connect_fn):
            from sync.readers.pg_cdc_reader import PostgresCdcReader

            reader = PostgresCdcReader(
                {"host": "realdb", "port": 5432, "database": "proddb", "username": "usr", "password": "pwd"},
                "ds-1",
                "tbl",
            )
            reader_ref[0] = reader

            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "events.jsonl"
                await reader.start_streaming(path, mock_on_event)

                assert path.exists()
                content = path.read_text(encoding="utf-8")
                assert "Alice" in content
                assert mock_on_event.called

    async def test_start_streaming_replication_publication_exists(self):
        """Cover lines 60-61: publication already exists, skip creation."""
        import tempfile
        from pathlib import Path
        from unittest.mock import AsyncMock, MagicMock, patch

        # Cursor returns a row (publication exists) → skip CREATE PUBLICATION
        mock_check_cursor = AsyncMock()
        mock_check_cursor.fetchone = AsyncMock(return_value=(1,))  # publication exists
        mock_check_cursor.execute = AsyncMock()

        mock_check_conn = AsyncMock()
        mock_check_conn.cursor = MagicMock(return_value=mock_check_cursor)
        mock_check_conn.__aenter__ = AsyncMock(return_value=mock_check_conn)
        mock_check_conn.__aexit__ = AsyncMock(return_value=None)

        # Replication connection that immediately stops
        mock_repl_conn = AsyncMock()

        reader_ref = [None]

        async def mock_receive():
            # Stop reader on first call — only need to verify publication-exists path
            if reader_ref[0]:
                reader_ref[0].running = False
            return None

        mock_repl_conn.receive = mock_receive
        mock_repl_conn.send_feedback = MagicMock()
        mock_repl_cursor = AsyncMock()
        mock_repl_cursor.execute = AsyncMock()
        mock_repl_conn.cursor = MagicMock(return_value=mock_repl_cursor)
        mock_repl_conn.__aenter__ = AsyncMock(return_value=mock_repl_conn)
        mock_repl_conn.__aexit__ = AsyncMock(return_value=None)

        connect_calls = [mock_check_conn, mock_repl_conn]
        call_idx = [0]

        async def mock_connect_fn(*args, **kwargs):
            idx = call_idx[0]
            call_idx[0] += 1
            return connect_calls[idx]

        mock_on_event = MagicMock()

        with patch("sync.readers.pg_cdc_reader.psycopg.AsyncConnection.connect", mock_connect_fn):
            from sync.readers.pg_cdc_reader import PostgresCdcReader

            reader = PostgresCdcReader(
                {"host": "realdb", "port": 5432, "database": "proddb", "username": "usr", "password": "pwd"},
                "ds-1",
                "tbl",
            )
            reader_ref[0] = reader

            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "events.jsonl"
                await reader.start_streaming(path, mock_on_event)

                # No message written since receive() returned None and loop stopped
                assert not path.exists() or path.read_text(encoding="utf-8").strip() == ""

    async def test_start_streaming_replication_inner_error(self):
        """Cover lines 106-108: inner exception in replication loop caught, continues."""
        import tempfile
        from pathlib import Path
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_check_cursor = AsyncMock()
        mock_check_cursor.fetchone = AsyncMock(return_value=(1,))
        mock_check_cursor.execute = AsyncMock()

        mock_check_conn = AsyncMock()
        mock_check_conn.cursor = MagicMock(return_value=mock_check_cursor)
        mock_check_conn.__aenter__ = AsyncMock(return_value=mock_check_conn)
        mock_check_conn.__aexit__ = AsyncMock(return_value=None)

        # Replication connection - first call raises, second stops loop
        receive_calls = [0]

        async def mock_receive():
            receive_calls[0] += 1
            if receive_calls[0] == 1:
                raise RuntimeError("replication read error")
            return None

        mock_repl_conn = AsyncMock()
        mock_repl_conn.receive = mock_receive
        mock_repl_conn.send_feedback = MagicMock()
        mock_repl_cursor = AsyncMock()
        mock_repl_cursor.execute = AsyncMock()
        mock_repl_conn.cursor = MagicMock(return_value=mock_repl_cursor)
        mock_repl_conn.__aenter__ = AsyncMock(return_value=mock_repl_conn)
        mock_repl_conn.__aexit__ = AsyncMock(return_value=None)

        connect_calls = [mock_check_conn, mock_repl_conn]
        call_idx = [0]

        async def mock_connect_fn(*args, **kwargs):
            idx = call_idx[0]
            call_idx[0] += 1
            return connect_calls[idx]

        mock_on_event = MagicMock()

        with patch("sync.readers.pg_cdc_reader.psycopg.AsyncConnection.connect", mock_connect_fn):
            from sync.readers.pg_cdc_reader import PostgresCdcReader

            reader = PostgresCdcReader(
                {"host": "realdb", "port": 5432, "database": "proddb", "username": "usr", "password": "pwd"},
                "ds-1",
                "tbl",
            )

            # After the error is caught, the second receive returns None and we stop
            async def receive_stop_on_second():
                receive_calls[0] += 1
                if receive_calls[0] <= 1:
                    raise RuntimeError("replication read error")
                reader.running = False
                return None

            receive_calls[0] = 0
            mock_repl_conn.receive = receive_stop_on_second

            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "events.jsonl"
                await reader.start_streaming(path, mock_on_event)

            # Should not have crashed
            assert reader.running is False

    async def test_start_streaming_replication_cancelled_error(self):
        """Cover lines 104-105: CancelledError in replication loop breaks out."""
        import tempfile
        from pathlib import Path
        from unittest.mock import AsyncMock, MagicMock, patch

        mock_check_cursor = AsyncMock()
        mock_check_cursor.fetchone = AsyncMock(return_value=(1,))
        mock_check_cursor.execute = AsyncMock()

        mock_check_conn = AsyncMock()
        mock_check_conn.cursor = MagicMock(return_value=mock_check_cursor)
        mock_check_conn.__aenter__ = AsyncMock(return_value=mock_check_conn)
        mock_check_conn.__aexit__ = AsyncMock(return_value=None)

        async def raise_cancelled():
            raise asyncio.CancelledError()

        mock_repl_conn = AsyncMock()
        mock_repl_conn.receive = raise_cancelled
        mock_repl_conn.send_feedback = MagicMock()
        mock_repl_cursor = AsyncMock()
        mock_repl_cursor.execute = AsyncMock()
        mock_repl_conn.cursor = MagicMock(return_value=mock_repl_cursor)
        mock_repl_conn.__aenter__ = AsyncMock(return_value=mock_repl_conn)
        mock_repl_conn.__aexit__ = AsyncMock(return_value=None)

        connect_calls = [mock_check_conn, mock_repl_conn]
        call_idx = [0]

        async def mock_connect_fn(*args, **kwargs):
            idx = call_idx[0]
            call_idx[0] += 1
            return connect_calls[idx]

        mock_on_event = MagicMock()

        with patch("sync.readers.pg_cdc_reader.psycopg.AsyncConnection.connect", mock_connect_fn):
            from sync.readers.pg_cdc_reader import PostgresCdcReader

            reader = PostgresCdcReader(
                {"host": "realdb", "port": 5432, "database": "proddb", "username": "usr", "password": "pwd"},
                "ds-1",
                "tbl",
            )

            # CancelledError breaks the loop but doesn't crash the method
            with tempfile.TemporaryDirectory() as tmpdir:
                path = Path(tmpdir) / "events.jsonl"
                await reader.start_streaming(path, mock_on_event)

            # Should exit cleanly despite CancelledError in inner loop
            assert reader.running is True  # was set True at start, CancelledError breaks loop but doesn't set False
