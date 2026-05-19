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


class TestExternalDbSyncService:
    @pytest.mark.asyncio
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_skips_datasets_without_sync_mode(self, mock_store, mock_get_adapter):
        session = _make_session()
        try:
            repo = DatasetRepository(session)
            # Create a dataset with sync_mode=None (should be skipped)
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
    @patch("sync.external_sync_service.get_adapter")
    @patch("sync.external_sync_service.AesGcmSecretStore")
    async def test_syncs_batch_dataset(self, mock_store, mock_get_adapter):
        session = _make_session()
        try:
            from connection.domain import Connection
            from connection.repository import ConnectionRepository

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

            mock_adapter = AsyncMock()
            mock_adapter.preview_table.return_value = {
                "columns": [{"name": "id", "data_type": "bigint"}, {"name": "name", "data_type": "varchar"}],
                "rows": [[1, "Alice"], [2, "Bob"]],
                "detected_cursor_column": None,
            }
            mock_get_adapter.return_value = mock_adapter

            service = ExternalDbSyncService(session)
            result = await service.run_async()

            assert result.status == "completed"
            assert len(result.snapshots) == 1
            assert result.snapshots[0].entity_type == "users"
            assert result.snapshots[0].row_count == 2
        finally:
            session.close()
