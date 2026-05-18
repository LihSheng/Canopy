import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from common.database import Base
from source_type.domain import SourceType, SourceTypeCategory
from source_type.repository import SourceTypeRepository
from source_type.service import SourceTypeService, _SEED_TYPES


@pytest.fixture(autouse=True)
def _setup_db():
    """Override conftest._setup_db to avoid PostgreSQL dependency."""
    yield


def _make_sqlite_session():
    engine = create_engine("sqlite:///", connect_args={"check_same_thread": False})
    import source_type.schema  # noqa: F401
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


class TestSeedTypes:
    def test_static_file_is_enabled(self):
        for entry in _SEED_TYPES:
            if entry["key"] == "static_file":
                assert entry["enabled"] is True
                break
        else:
            pytest.fail("static_file not found in _SEED_TYPES")

    def test_mysql_is_disabled(self):
        for entry in _SEED_TYPES:
            if entry["key"] == "mysql":
                assert entry["enabled"] is False
                break
        else:
            pytest.fail("mysql not found in _SEED_TYPES")

    def test_all_six_types_present(self):
        keys = {entry["key"] for entry in _SEED_TYPES}
        expected = {"static_file", "mysql", "postgresql", "rest_api", "google_sheets", "csv"}
        assert keys == expected

    def test_static_file_category_is_file(self):
        for entry in _SEED_TYPES:
            if entry["key"] == "static_file":
                assert entry["category"] == SourceTypeCategory.FILE.value
                break

    def test_mysql_category_is_database(self):
        for entry in _SEED_TYPES:
            if entry["key"] == "mysql":
                assert entry["category"] == SourceTypeCategory.DATABASE.value
                break

    def test_rest_api_category_is_api(self):
        for entry in _SEED_TYPES:
            if entry["key"] == "rest_api":
                assert entry["category"] == SourceTypeCategory.API.value
                break


class TestSourceTypeService:
    def test_ensure_seeded_populates_all_types(self):
        session = _make_sqlite_session()
        try:
            repo = SourceTypeRepository(session)
            service = SourceTypeService(repo)
            service.ensure_seeded()
            types = service.list_source_types()
            assert len(types) == 6
        finally:
            session.close()

    def test_ensure_seeded_is_idempotent(self):
        session = _make_sqlite_session()
        try:
            repo = SourceTypeRepository(session)
            service = SourceTypeService(repo)
            service.ensure_seeded()
            first_count = len(service.list_source_types())
            service.ensure_seeded()
            second_count = len(service.list_source_types())
            assert second_count == first_count == 6
        finally:
            session.close()

    def test_list_source_types_returns_all_keys(self):
        session = _make_sqlite_session()
        try:
            repo = SourceTypeRepository(session)
            service = SourceTypeService(repo)
            service.ensure_seeded()
            types = service.list_source_types()
            keys = {t.key for t in types}
            assert keys == {"static_file", "mysql", "postgresql", "rest_api", "google_sheets", "csv"}
        finally:
            session.close()

    def test_get_enabled_returns_only_static_file(self):
        session = _make_sqlite_session()
        try:
            repo = SourceTypeRepository(session)
            service = SourceTypeService(repo)
            service.ensure_seeded()
            enabled = service.get_enabled()
            assert len(enabled) == 1
            assert enabled[0].key == "static_file"
            assert enabled[0].enabled is True
        finally:
            session.close()

    def test_get_enabled_excludes_disabled_types(self):
        session = _make_sqlite_session()
        try:
            repo = SourceTypeRepository(session)
            service = SourceTypeService(repo)
            service.ensure_seeded()
            enabled = service.get_enabled()
            enabled_keys = {t.key for t in enabled}
            assert "mysql" not in enabled_keys
            assert "postgresql" not in enabled_keys
        finally:
            session.close()

    def test_ensure_seeded_with_mock_repo(self):
        repo = MagicMock(spec=SourceTypeRepository)
        repo.list_all.return_value = []
        service = SourceTypeService(repo)
        service.ensure_seeded()
        assert repo.save.call_count == 6

    def test_list_source_types_delegates_to_repo(self):
        repo = MagicMock(spec=SourceTypeRepository)
        repo.list_all.return_value = []
        service = SourceTypeService(repo)
        service.list_source_types()
        repo.list_all.assert_called_once()

    def test_get_enabled_delegates_to_repo(self):
        repo = MagicMock(spec=SourceTypeRepository)
        repo.get_enabled.return_value = []
        service = SourceTypeService(repo)
        service.get_enabled()
        repo.get_enabled.assert_called_once()


class TestSourceTypeRepository:
    def test_get_by_key_finds_existing_type(self):
        session = _make_sqlite_session()
        try:
            repo = SourceTypeRepository(session)
            service = SourceTypeService(repo)
            service.ensure_seeded()
            st = repo.get_by_key("mysql")
            assert st is not None
            assert st.key == "mysql"
            assert st.label == "MySQL"
            assert st.enabled is False
        finally:
            session.close()

    def test_get_by_key_returns_none_for_missing_key(self):
        session = _make_sqlite_session()
        try:
            repo = SourceTypeRepository(session)
            result = repo.get_by_key("nonexistent_key")
            assert result is None
        finally:
            session.close()

    def test_get_by_key_returns_none_for_nonexistent_key(self):
        session = _make_sqlite_session()
        try:
            repo = SourceTypeRepository(session)
            service = SourceTypeService(repo)
            service.ensure_seeded()
            result = repo.get_by_key("mongodb")
            assert result is None
        finally:
            session.close()

    def test_list_all_returns_all_seeded_types(self):
        session = _make_sqlite_session()
        try:
            repo = SourceTypeRepository(session)
            service = SourceTypeService(repo)
            service.ensure_seeded()
            all_types = repo.list_all()
            assert len(all_types) == 6
        finally:
            session.close()

    def test_save_persists_source_type(self):
        session = _make_sqlite_session()
        try:
            repo = SourceTypeRepository(session)
            st = SourceType(
                id=str(uuid.uuid4()),
                key="test_key",
                label="Test Label",
                category="file",
                enabled=True,
                tags=["test"],
                description="A test type",
            )
            saved = repo.save(st)
            assert saved.id == st.id
            assert saved.key == "test_key"

            fetched = repo.get_by_key("test_key")
            assert fetched is not None
            assert fetched.label == "Test Label"
        finally:
            session.close()
