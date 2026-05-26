from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common.config import settings
from common.database import Base
from connection.domain import Connection
from connection.repository import ConnectionRepository
from dataset.repository import DatasetRepository, DatasetVersionRepository
from dataset.service import DatasetService


class _MockMySqlAdapter:
    async def fetch_table(self, config: dict, table: str, cursor_column=None, cursor_value=None):
        async def _rows():
            yield [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"},
            ]

        return _rows()


def _make_session():
    engine = create_engine("sqlite:///", connect_args={"check_same_thread": False})
    import connection.schema  # noqa: F401
    import dataset.schema  # noqa: F401

    Base.metadata.create_all(bind=engine)
    session_local = sessionmaker(bind=engine)
    return session_local()


def test_create_mysql_dataset_materializes_initial_version(tmp_path, monkeypatch):
    session = _make_session()
    try:
        conn_repo = ConnectionRepository(session)
        conn_repo.save(
            Connection(
                id="conn-1",
                project_id="proj-1",
                source_type="mysql",
                name="MySQL",
                config_json={"host": "127.0.0.1", "database": "tenant_demo", "username": "homestead"},
            )
        )

        service = DatasetService(DatasetRepository(session), DatasetVersionRepository(session))
        monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)
        with patch("dataset.service.get_adapter", return_value=_MockMySqlAdapter()):
            dataset = service.create_dataset(
                project_id="proj-1",
                connection_id="conn-1",
                name="org_leave_type",
                source_object_name="org_leave_type",
                sync_mode="batch",
                batch_strategy="full_snapshot",
            )

        assert dataset.active_version_id is not None
        preview = service.preview_dataset(dataset.id, page=1, page_size=10)
        assert preview["columns"] == ["id", "name"]
        assert preview["rows"] == [[1, "Alice"], [2, "Bob"]]
        assert preview["total_row_count"] == 2

        version = DatasetVersionRepository(session).get_active_version(dataset.id, dataset.active_version_id)
        assert version is not None
        assert version.row_count == 2
        assert version.column_count == 2
        assert Path(version.storage_path).exists()
    finally:
        session.close()
