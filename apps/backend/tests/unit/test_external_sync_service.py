"""Tests for ExternalDbSyncService."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from dataset.domain import Dataset, DatasetStatus, SyncMode
from dataset.repository import DatasetRepository
from sync.external_sync_service import ExternalDbSyncService
from tests.unit.postgres_test_db import make_postgres_session


@pytest.fixture(autouse=True)
def _setup_db():
    yield


def _make_session():
    return make_postgres_session(("connection.schema", "dataset.schema"))


class MockCursorHelper:
    """Helper to create an async generator for mocking DatabaseAdapter.fetch_table."""

    @staticmethod
    async def batches(*batches: list[dict]):
        for batch in batches:
            yield batch

    @staticmethod
    def fetch_table_callback(rows: list[dict]):
        """Return an async callable that returns an async generator yielding the given rows."""

        async def _fetch(config, table, cursor_column=None, cursor_value=None):
            async def _generate():
                yield rows

            return _generate()

        return _fetch


class TestExternalDbSyncService:
    @pytest.mark.asyncio
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_skips_datasets_without_sync_mode(self, mock_store, mock_get_adapter):
        session = _make_session()
        try:
            repo = DatasetRepository(session)
            repo.save(
                Dataset(
                    id="ds-1",
                    project_id="p-1",
                    connection_id="c-1",
                    name="no_sync",
                    status=DatasetStatus.ACTIVE.value,
                )
            )

            service = ExternalDbSyncService(session)
            result = await service.run_async()

            assert result.status == "completed"
            assert len(result.snapshots) == 0
        finally:
            session.close()

    @pytest.mark.asyncio
    @patch("sync.external_sync_service.ExternalDbSyncService._write_rows_to_storage")
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_syncs_batch_dataset(self, mock_store, mock_get_adapter, mock_write):
        session = _make_session()
        try:
            from connection.domain import Connection
            from connection.repository import ConnectionRepository

            # Seed connection + dataset
            conn_repo = ConnectionRepository(session)
            conn_repo.save(
                Connection(
                    id="c-1",
                    project_id="p-1",
                    source_type="postgresql",
                    name="test",
                    config_json={"host": "localhost"},
                )
            )

            repo = DatasetRepository(session)
            repo.save(
                Dataset(
                    id="ds-1",
                    project_id="p-1",
                    connection_id="c-1",
                    name="users",
                    source_object_name="users",
                    status=DatasetStatus.ACTIVE.value,
                    sync_mode=SyncMode.BATCH,
                    batch_strategy="full_snapshot",
                )
            )

            # Mock fetch_table to return rows
            mock_adapter = AsyncMock()
            rows_batch = [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]
            mock_adapter.fetch_table = MockCursorHelper.fetch_table_callback(rows_batch)
            mock_get_adapter.return_value = mock_adapter

            # Prevent actual disk I/O
            mock_write.return_value = "/mock/storage/users.jsonl"

            service = ExternalDbSyncService(session)
            result = await service.run_async()

            assert result.status == "completed"
            assert len(result.snapshots) == 1
            assert result.snapshots[0].entity_type == "users"
            assert result.snapshots[0].row_count == 2

            # Verify storage was persisted
            mock_write.assert_called_once()
            args, _ = mock_write.call_args
            assert len(args[2]) == 2  # Two rows persisted
        finally:
            session.close()

    @pytest.mark.asyncio
    @patch("sync.external_sync_service.ExternalDbSyncService._write_rows_to_storage")
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_incremental_cursor_updates_cursor_value(self, mock_store, mock_get_adapter, mock_write):
        session = _make_session()
        try:
            from connection.domain import Connection
            from connection.repository import ConnectionRepository

            conn_repo = ConnectionRepository(session)
            conn_repo.save(
                Connection(
                    id="c-2",
                    project_id="p-1",
                    source_type="postgresql",
                    name="test",
                    config_json={"host": "localhost"},
                )
            )

            repo = DatasetRepository(session)
            repo.save(
                Dataset(
                    id="ds-2",
                    project_id="p-1",
                    connection_id="c-2",
                    name="orders",
                    source_object_name="orders",
                    status=DatasetStatus.ACTIVE.value,
                    sync_mode=SyncMode.BATCH,
                    batch_strategy="incremental_cursor",
                    cursor_column="updated_at",
                    last_cursor_value="2026-01-01T00:00:00Z",
                )
            )

            rows_batch = [
                {"id": 1, "updated_at": "2026-06-01T00:00:00Z"},
                {"id": 2, "updated_at": "2026-06-15T00:00:00Z"},
            ]
            mock_adapter = AsyncMock()
            mock_adapter.fetch_table = MockCursorHelper.fetch_table_callback(rows_batch)
            mock_get_adapter.return_value = mock_adapter
            mock_write.return_value = "/mock/storage/orders.jsonl"

            service = ExternalDbSyncService(session)
            result = await service.run_async()

            assert result.status == "completed"
            assert result.snapshots[0].row_count == 2

            # Verify cursor was updated to the max value
            updated = repo.get("ds-2")
            assert updated is not None
            assert updated.last_cursor_value == "2026-06-15T00:00:00Z"
        finally:
            session.close()

    @pytest.mark.asyncio
    @patch("sync.readers.pg_cdc_reader.PostgresCdcReader")
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_cdc_dataset_uses_log_streaming_instead_of_table_polling(
        self,
        mock_store,
        mock_get_adapter,
        mock_reader_cls,
    ):
        session = _make_session()
        try:
            from connection.domain import Connection
            from connection.repository import ConnectionRepository

            conn_repo = ConnectionRepository(session)
            conn_repo.save(
                Connection(
                    id="c-3",
                    project_id="p-1",
                    source_type="postgresql",
                    name="cdc",
                    config_json={"host": "localhost", "supports_cdc": True},
                )
            )

            repo = DatasetRepository(session)
            repo.save(
                Dataset(
                    id="ds-3",
                    project_id="p-1",
                    connection_id="c-3",
                    name="events",
                    source_object_name="events",
                    status=DatasetStatus.ACTIVE.value,
                    sync_mode=SyncMode.REAL_TIME,
                    real_time_strategy="cdc",
                )
            )

            mock_adapter = AsyncMock()
            mock_adapter.fetch_table = AsyncMock()
            mock_get_adapter.return_value = mock_adapter

            reader_instance = AsyncMock()
            reader_instance.start_streaming = AsyncMock(return_value=None)
            mock_reader_cls.return_value = reader_instance

            service = ExternalDbSyncService(session)
            result = await service.run_async()
            await asyncio.sleep(0)

            assert result.status == "completed"
            mock_adapter.fetch_table.assert_not_called()
            mock_reader_cls.assert_called_once()
            reader_instance.start_streaming.assert_called_once()
        finally:
            session.close()

    @pytest.mark.asyncio
    @patch("sync.external_sync_service.ExternalDbSyncService._write_rows_to_storage")
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_partial_failure_sets_partial_status(self, mock_store, mock_get_adapter, mock_write):
        """line 74: some succeed, some fail -> status='partial'."""
        from connection.domain import Connection
        from connection.repository import ConnectionRepository

        session = _make_session()
        try:
            conn_repo = ConnectionRepository(session)
            conn_repo.save(
                Connection(id="c-partial", project_id="p-1", source_type="postgresql", name="test", config_json={})
            )

            repo = DatasetRepository(session)
            repo.save(
                Dataset(
                    id="ds-good",
                    project_id="p-1",
                    connection_id="c-partial",
                    name="good",
                    status=DatasetStatus.ACTIVE.value,
                    sync_mode=SyncMode.BATCH,
                    batch_strategy="full_snapshot",
                )
            )
            repo.save(
                Dataset(
                    id="ds-bad",
                    project_id="p-1",
                    connection_id="c-partial",
                    name="bad",
                    status=DatasetStatus.ACTIVE.value,
                    sync_mode=SyncMode.BATCH,
                    batch_strategy="full_snapshot",
                )
            )

            mock_adapter = AsyncMock()
            rows_batch = [{"id": 1, "name": "Alice"}]
            mock_adapter.fetch_table = MockCursorHelper.fetch_table_callback(rows_batch)
            mock_get_adapter.return_value = mock_adapter
            mock_write.return_value = "/mock/storage/good.jsonl"

            from sync.external_sync_service import ExternalDbSyncService

            original_sync_one = ExternalDbSyncService._sync_one

            async def side_effect(self, ds, started_at):
                if ds.name == "bad":
                    raise RuntimeError("conn refused")
                return await original_sync_one(self, ds, started_at)

            with patch.object(ExternalDbSyncService, "_sync_one", side_effect):
                service = ExternalDbSyncService(session)
                result = await service.run_async()

            assert result.status == "partial"
        finally:
            session.close()

    @pytest.mark.asyncio
    @patch("sync.readers.mysql_cdc_reader.MysqlCdcReader")
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_cdc_dataset_uses_mysql_reader(
        self,
        mock_store,
        mock_get_adapter,
        mock_reader_cls,
    ):
        """lines 121-123: MySQL CDC reader for MySQL source type."""
        from connection.domain import Connection
        from connection.repository import ConnectionRepository

        session = _make_session()
        try:
            conn_repo = ConnectionRepository(session)
            conn_repo.save(
                Connection(
                    id="c-mysql",
                    project_id="p-1",
                    source_type="mysql",
                    name="mysql-cdc",
                    config_json={"host": "localhost", "supports_cdc": True},
                )
            )

            repo = DatasetRepository(session)
            repo.save(
                Dataset(
                    id="ds-mysql-cdc",
                    project_id="p-1",
                    connection_id="c-mysql",
                    name="mysql_events",
                    source_object_name="mysql_events",
                    status=DatasetStatus.ACTIVE.value,
                    sync_mode=SyncMode.REAL_TIME,
                    real_time_strategy="cdc",
                )
            )

            mock_adapter = AsyncMock()
            mock_adapter.fetch_table = AsyncMock()
            mock_get_adapter.return_value = mock_adapter

            reader_instance = AsyncMock()
            reader_instance.start_streaming = AsyncMock(return_value=None)
            mock_reader_cls.return_value = reader_instance

            service = ExternalDbSyncService(session)
            result = await service.run_async()
            await asyncio.sleep(0)

            assert result.status == "completed"
            mock_adapter.fetch_table.assert_not_called()
            mock_reader_cls.assert_called_once()
            reader_instance.start_streaming.assert_called_once()
        finally:
            session.close()

    @pytest.mark.asyncio
    @patch("sync.readers.mysql_cdc_reader.MysqlCdcReader")
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_cdc_storage_path_read_error_handled(
        self,
        mock_store,
        mock_get_adapter,
        mock_reader_cls,
    ):
        """lines 129-133: exception reading storage_path is handled."""

        from connection.domain import Connection
        from connection.repository import ConnectionRepository

        session = _make_session()
        try:
            conn_repo = ConnectionRepository(session)
            conn_repo.save(
                Connection(
                    id="c-storage",
                    project_id="p-1",
                    source_type="mysql",
                    name="storage-test",
                    config_json={"host": "localhost", "supports_cdc": True},
                )
            )

            repo = DatasetRepository(session)
            repo.save(
                Dataset(
                    id="ds-storage",
                    project_id="p-1",
                    connection_id="c-storage",
                    name="storage_events",
                    source_object_name="storage_events",
                    status=DatasetStatus.ACTIVE.value,
                    sync_mode=SyncMode.REAL_TIME,
                    real_time_strategy="cdc",
                )
            )

            mock_adapter = AsyncMock()
            mock_get_adapter.return_value = mock_adapter

            reader_instance = AsyncMock()
            reader_instance.start_streaming = AsyncMock(return_value=None)
            mock_reader_cls.return_value = reader_instance

            from pathlib import Path

            with (
                patch.object(Path, "exists", return_value=True),
                patch("builtins.open", side_effect=OSError("read error")),
            ):
                service = ExternalDbSyncService(session)
                result = await service.run_async()
                await asyncio.sleep(0)

            assert result.status == "completed"
        finally:
            session.close()

    @pytest.mark.asyncio
    @patch("sync.readers.mysql_cdc_reader.MysqlCdcReader")
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_cdc_storage_path_read_success(
        self,
        mock_store,
        mock_get_adapter,
        mock_reader_cls,
    ):
        """line 131: successful file read counts rows."""
        import io

        from connection.domain import Connection
        from connection.repository import ConnectionRepository

        session = _make_session()
        try:
            conn_repo = ConnectionRepository(session)
            conn_repo.save(
                Connection(
                    id="c-count",
                    project_id="p-1",
                    source_type="mysql",
                    name="count-test",
                    config_json={"host": "localhost", "supports_cdc": True},
                )
            )

            repo = DatasetRepository(session)
            repo.save(
                Dataset(
                    id="ds-count",
                    project_id="p-1",
                    connection_id="c-count",
                    name="count_events",
                    source_object_name="count_events",
                    status=DatasetStatus.ACTIVE.value,
                    sync_mode=SyncMode.REAL_TIME,
                    real_time_strategy="cdc",
                )
            )

            mock_adapter = AsyncMock()
            mock_get_adapter.return_value = mock_adapter

            reader_instance = AsyncMock()
            reader_instance.start_streaming = AsyncMock(return_value=None)
            mock_reader_cls.return_value = reader_instance

            from pathlib import Path

            mock_file = io.StringIO("line1\nline2\nline3\n")
            with patch.object(Path, "exists", return_value=True), patch("builtins.open", return_value=mock_file):
                service = ExternalDbSyncService(session)
                result = await service.run_async()
                await asyncio.sleep(0)

            assert result.status == "completed"
        finally:
            session.close()

    @pytest.mark.asyncio
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_connection_not_found_raises_error(self, mock_store, mock_get_adapter):
        """line 81: conn is None raises NotFoundError."""
        session = _make_session()
        try:
            from dataset.repository import DatasetRepository

            repo = DatasetRepository(session)
            repo.save(
                Dataset(
                    id="ds-orphan",
                    project_id="p-1",
                    connection_id="c-missing",
                    name="orphan",
                    status=DatasetStatus.ACTIVE.value,
                    sync_mode=SyncMode.BATCH,
                    batch_strategy="full_snapshot",
                )
            )

            service = ExternalDbSyncService(session)
            result = await service.run_async()

            # The dataset with missing connection should fail gracefully
            assert len(result.snapshots) > 0
            assert result.snapshots[0].status == "failed"
            assert result.snapshots[0].error_message is not None
        finally:
            session.close()

    @pytest.mark.asyncio
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_connection_password_decryption(self, mock_store, mock_get_adapter):
        """line 85: password decryption from secret store."""
        from connection.domain import Connection
        from connection.repository import ConnectionRepository

        session = _make_session()
        try:
            conn_repo = ConnectionRepository(session)
            conn_repo.save(
                Connection(
                    id="c-1",
                    project_id="p-1",
                    source_type="postgresql",
                    name="test",
                    config_json={"password": "encrypted_value"},
                )
            )

            repo = DatasetRepository(session)
            repo.save(
                Dataset(
                    id="ds-1",
                    project_id="p-1",
                    connection_id="c-1",
                    name="users",
                    status=DatasetStatus.ACTIVE.value,
                    sync_mode=SyncMode.BATCH,
                    batch_strategy="full_snapshot",
                )
            )

            # Mock the secret store to return a decrypted password
            mock_store_instance = AsyncMock()
            mock_store_instance.decrypt.return_value = "decrypted_pass"
            mock_store.return_value = mock_store_instance

            mock_adapter = AsyncMock()
            mock_adapter.fetch_table = MockCursorHelper.fetch_table_callback([])
            mock_get_adapter.return_value = mock_adapter

            with patch(
                "sync.external_sync_service.ExternalDbSyncService._write_rows_to_storage",
                return_value="/mock/path.jsonl",
            ):
                service = ExternalDbSyncService(session)
                result = await service.run_async()

            assert result.status == "completed"
        finally:
            session.close()


class TestWriteRowsToStorage:
    """Cover _write_rows_to_storage (lines 200-207)."""

    @patch("pathlib.Path.mkdir")
    @patch("builtins.open")
    def test_writes_jsonl(self, mock_open, mock_mkdir):
        from sync.external_sync_service import ExternalDbSyncService

        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        result = ExternalDbSyncService._write_rows_to_storage("ds-1", "users", rows)
        assert result is not None
        assert str(result).endswith(".jsonl")
        mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
        assert mock_open.called
