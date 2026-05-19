"""Tests for ExternalDbSyncService."""
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common.database import Base
from dataset.domain import Dataset, DatasetStatus, SyncMode
from dataset.repository import DatasetRepository
from sync.external_sync_service import ExternalDbSyncService


@pytest.fixture(autouse=True)
def _setup_db():
    yield


def _make_session():
    engine = create_engine("sqlite:///", connect_args={"check_same_thread": False})
    import dataset.schema  # noqa: F401
    import connection.schema  # noqa: F401
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


class MockCursorHelper:
    """Helper to create an async generator for mocking DatabaseAdapter.fetch_table."""

    @staticmethod
    async def batches(*batches: list[dict]):
        for batch in batches:
            yield batch

    @staticmethod
    def fetch_table_callback(rows: list[dict]):
        """Return a callable that returns an async generator yielding the given rows."""
        async def _fetch(config, table, cursor_column=None, cursor_value=None):
            yield rows
        return _fetch


class TestExternalDbSyncService:
    @pytest.mark.asyncio
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_skips_datasets_without_sync_mode(self, mock_store, mock_get_adapter):
        session = _make_session()
        try:
            repo = DatasetRepository(session)
            repo.save(Dataset(
                id="ds-1", project_id="p-1", connection_id="c-1",
                name="no_sync", status=DatasetStatus.ACTIVE.value,
            ))

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
            conn_repo.save(Connection(
                id="c-1", project_id="p-1", source_type="postgresql",
                name="test", config_json={"host": "localhost"},
            ))

            repo = DatasetRepository(session)
            repo.save(Dataset(
                id="ds-1", project_id="p-1", connection_id="c-1",
                name="users", source_object_name="users",
                status=DatasetStatus.ACTIVE.value,
                sync_mode=SyncMode.BATCH, batch_strategy="full_snapshot",
            ))

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
            conn_repo.save(Connection(
                id="c-2", project_id="p-1", source_type="postgresql",
                name="test", config_json={"host": "localhost"},
            ))

            repo = DatasetRepository(session)
            repo.save(Dataset(
                id="ds-2", project_id="p-1", connection_id="c-2",
                name="orders", source_object_name="orders",
                status=DatasetStatus.ACTIVE.value,
                sync_mode=SyncMode.BATCH,
                batch_strategy="incremental_cursor",
                cursor_column="updated_at",
                last_cursor_value="2026-01-01T00:00:00Z",
            ))

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
