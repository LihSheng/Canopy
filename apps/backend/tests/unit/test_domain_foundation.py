"""Tests for domain foundation: SyncMode, BatchStrategy, Dataset sync fields."""

from datetime import UTC, datetime

import pytest

from dataset.domain import (
    BatchStrategy,
    Dataset,
    SyncMode,
)


class TestSyncMode:
    def test_batch_value(self):
        assert SyncMode.BATCH == "batch"

    def test_real_time_value(self):
        assert SyncMode.REAL_TIME == "real_time"

    def test_direct_query_value(self):
        assert SyncMode.DIRECT_QUERY == "direct_query"


class TestBatchStrategy:
    def test_full_snapshot_value(self):
        assert BatchStrategy.FULL_SNAPSHOT == "full_snapshot"

    def test_incremental_cursor_value(self):
        assert BatchStrategy.INCREMENTAL_CURSOR == "incremental_cursor"


class TestDatasetSyncFields:
    def test_creates_with_default_sync_mode(self):
        ds = Dataset(
            id="ds-1",
            project_id="p-1",
            connection_id="c-1",
            name="test",
        )
        assert ds.sync_mode is None

    def test_creates_with_batch_sync_mode(self):
        ds = Dataset(
            id="ds-1",
            project_id="p-1",
            connection_id="c-1",
            name="test",
            sync_mode=SyncMode.BATCH,
        )
        assert ds.sync_mode == "batch"

    def test_creates_with_incremental_cursor(self):
        ds = Dataset(
            id="ds-1",
            project_id="p-1",
            connection_id="c-1",
            name="test",
            sync_mode=SyncMode.BATCH,
            batch_strategy=BatchStrategy.INCREMENTAL_CURSOR,
            cursor_column="updated_at",
            last_cursor_value="2026-05-19T00:00:00Z",
        )
        assert ds.batch_strategy == "incremental_cursor"
        assert ds.cursor_column == "updated_at"
        assert ds.last_cursor_value == "2026-05-19T00:00:00Z"


class TestConnectionTestFields:
    def test_default_test_status_is_none(self):
        from connection.domain import Connection

        conn = Connection(id="c-1", project_id="p-1", source_type="postgresql", name="test")
        assert conn.test_status is None
        assert conn.last_tested_at is None

    def test_creates_with_test_success(self):
        from connection.domain import Connection

        conn = Connection(
            id="c-1",
            project_id="p-1",
            source_type="postgresql",
            name="test",
            test_status="success",
            last_tested_at=datetime.now(UTC),
        )
        assert conn.test_status == "success"


class TestDatasetRepositorySyncFields:
    def test_save_and_retrieve_sync_fields(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import dataset.schema  # noqa: F401
        from common.database import Base
        from dataset.repository import DatasetRepository

        engine = create_engine("sqlite:///", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        session = sessionmaker(bind=engine)()
        repo = DatasetRepository(session)

        ds = Dataset(
            id="ds-1",
            project_id="p-1",
            connection_id="c-1",
            name="test_table",
            sync_mode=SyncMode.BATCH,
            batch_strategy=BatchStrategy.INCREMENTAL_CURSOR,
            cursor_column="updated_at",
        )
        saved = repo.save(ds)
        assert saved.sync_mode == "batch"
        assert saved.batch_strategy == "incremental_cursor"
        assert saved.cursor_column == "updated_at"

        retrieved = repo.get("ds-1")
        assert retrieved is not None
        assert retrieved.sync_mode == "batch"
        assert retrieved.batch_strategy == "incremental_cursor"
        assert retrieved.cursor_column == "updated_at"

        session.close()


class TestConnectionRepositoryTestFields:
    def test_save_and_retrieve_test_status(self):
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        import connection.schema  # noqa: F401
        from common.database import Base
        from connection.domain import Connection
        from connection.repository import ConnectionRepository

        engine = create_engine("sqlite:///", connect_args={"check_same_thread": False})
        Base.metadata.create_all(bind=engine)
        session = sessionmaker(bind=engine)()
        repo = ConnectionRepository(session)

        conn = Connection(
            id="c-1",
            project_id="p-1",
            source_type="postgresql",
            name="test",
            test_status="success",
            last_tested_at=datetime.now(UTC),
        )
        saved = repo.save(conn)
        assert saved.test_status == "success"

        retrieved = repo.get("c-1")
        assert retrieved is not None
        assert retrieved.test_status == "success"

        session.close()


class TestSourceTypeSeed:
    def test_postgresql_is_enabled_after_seed(self):
        from source_type.service import _SEED_TYPES

        for entry in _SEED_TYPES:
            if entry["key"] == "postgresql":
                assert entry["enabled"] is True
                break
        else:
            pytest.fail("postgresql not found")

    def test_mysql_is_enabled_after_seed(self):
        from source_type.service import _SEED_TYPES

        for entry in _SEED_TYPES:
            if entry["key"] == "mysql":
                assert entry["enabled"] is True
                break
        else:
            pytest.fail("mysql not found")
