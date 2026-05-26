import uuid

import pytest

from dataset.domain import Dataset, DatasetVersion
from dataset.repository import DatasetRepository, DatasetVersionRepository
from dataset.service import DatasetVersionService
from tests.unit.postgres_test_db import make_postgres_session


@pytest.fixture(autouse=True)
def _setup_db():
    """Keep the module isolated; sessions manage their own Postgres database."""
    yield


def _make_postgres_session():
    return make_postgres_session(("dataset.schema",))


class TestDatasetVersionService:
    def test_create_version_when_none_exist_returns_1(self):
        session = _make_postgres_session()
        try:
            version_repo = DatasetVersionRepository(session)
            dataset_repo = DatasetRepository(session)
            service = DatasetVersionService(version_repo, dataset_repo)
            version = service.create_version("ds-1")
            assert version.version_number == 1
            assert version.dataset_id == "ds-1"
        finally:
            session.close()

    def test_create_version_increments_version_number(self):
        session = _make_postgres_session()
        try:
            version_repo = DatasetVersionRepository(session)
            dataset_repo = DatasetRepository(session)
            service = DatasetVersionService(version_repo, dataset_repo)
            v1 = service.create_version("ds-1")
            v2 = service.create_version("ds-1")
            v3 = service.create_version("ds-1")
            assert v1.version_number == 1
            assert v2.version_number == 2
            assert v3.version_number == 3
        finally:
            session.close()

    def test_create_version_preserves_run_id(self):
        session = _make_postgres_session()
        try:
            version_repo = DatasetVersionRepository(session)
            dataset_repo = DatasetRepository(session)
            service = DatasetVersionService(version_repo, dataset_repo)
            version = service.create_version("ds-1", run_id="run-99")
            assert version.version_number == 1
            assert version.run_id == "run-99"
        finally:
            session.close()

    def test_create_version_default_status_is_pending(self):
        session = _make_postgres_session()
        try:
            version_repo = DatasetVersionRepository(session)
            dataset_repo = DatasetRepository(session)
            service = DatasetVersionService(version_repo, dataset_repo)
            version = service.create_version("ds-1")
            assert version.status == "pending"
        finally:
            session.close()

    def test_list_versions_returns_versions_from_repo(self):
        session = _make_postgres_session()
        try:
            version_repo = DatasetVersionRepository(session)
            dataset_repo = DatasetRepository(session)
            service = DatasetVersionService(version_repo, dataset_repo)
            service.create_version("ds-x")
            service.create_version("ds-x")
            versions = service.list_versions("ds-x")
            assert len(versions) == 2
        finally:
            session.close()

    def test_get_version_returns_version_by_id(self):
        session = _make_postgres_session()
        try:
            version_repo = DatasetVersionRepository(session)
            dataset_repo = DatasetRepository(session)
            service = DatasetVersionService(version_repo, dataset_repo)
            created = service.create_version("ds-1")
            fetched = service.get_version(created.id)
            assert fetched is not None
            assert fetched.id == created.id
            assert fetched.version_number == 1
        finally:
            session.close()

    def test_get_version_returns_none_for_missing(self):
        session = _make_postgres_session()
        try:
            version_repo = DatasetVersionRepository(session)
            dataset_repo = DatasetRepository(session)
            service = DatasetVersionService(version_repo, dataset_repo)
            result = service.get_version("nonexistent-id")
            assert result is None
        finally:
            session.close()


class TestDatasetVersionRepository:
    def test_list_by_dataset_returns_desc_order(self):
        session = _make_postgres_session()
        try:
            repo = DatasetVersionRepository(session)
            ds_id = str(uuid.uuid4())
            versions = [
                DatasetVersion(id=str(uuid.uuid4()), dataset_id=ds_id, version_number=1),
                DatasetVersion(id=str(uuid.uuid4()), dataset_id=ds_id, version_number=2),
                DatasetVersion(id=str(uuid.uuid4()), dataset_id=ds_id, version_number=3),
            ]
            for v in versions:
                repo.save(v)
            result = repo.list_by_dataset(ds_id)
            assert len(result) == 3
            assert result[0].version_number == 3
            assert result[1].version_number == 2
            assert result[2].version_number == 1
        finally:
            session.close()

    def test_get_latest_by_dataset_returns_highest_version(self):
        session = _make_postgres_session()
        try:
            repo = DatasetVersionRepository(session)
            ds_id = str(uuid.uuid4())
            repo.save(DatasetVersion(id=str(uuid.uuid4()), dataset_id=ds_id, version_number=1))
            repo.save(DatasetVersion(id=str(uuid.uuid4()), dataset_id=ds_id, version_number=5))
            repo.save(DatasetVersion(id=str(uuid.uuid4()), dataset_id=ds_id, version_number=3))
            latest = repo.get_latest_by_dataset(ds_id)
            assert latest is not None
            assert latest.version_number == 5
        finally:
            session.close()

    def test_get_latest_by_dataset_returns_none_for_empty(self):
        session = _make_postgres_session()
        try:
            repo = DatasetVersionRepository(session)
            result = repo.get_latest_by_dataset("no-such-dataset")
            assert result is None
        finally:
            session.close()

    def test_list_by_dataset_returns_empty_for_no_versions(self):
        session = _make_postgres_session()
        try:
            repo = DatasetVersionRepository(session)
            result = repo.list_by_dataset("no-such-dataset")
            assert result == []
        finally:
            session.close()

    def test_get_active_version_returns_matching_version(self):
        session = _make_postgres_session()
        try:
            repo = DatasetVersionRepository(session)
            ds_id = str(uuid.uuid4())
            v = DatasetVersion(id="ver-1", dataset_id=ds_id, version_number=1)
            repo.save(v)
            result = repo.get_active_version(ds_id, "ver-1")
            assert result is not None
            assert result.id == "ver-1"
        finally:
            session.close()

    def test_get_active_version_returns_none_for_mismatch(self):
        session = _make_postgres_session()
        try:
            repo = DatasetVersionRepository(session)
            ds_id = str(uuid.uuid4())
            v = DatasetVersion(id="ver-1", dataset_id=ds_id, version_number=1)
            repo.save(v)
            result = repo.get_active_version(ds_id, "wrong-ver-id")
            assert result is None
        finally:
            session.close()


class TestDatasetRepository:
    def test_update_active_version_sets_version_id(self):
        session = _make_postgres_session()
        try:
            repo = DatasetRepository(session)
            dataset = Dataset(
                id=str(uuid.uuid4()),
                project_id="proj-1",
                connection_id="conn-1",
                name="test-dataset",
            )
            saved = repo.save(dataset)
            assert saved.active_version_id is None
            version_id = str(uuid.uuid4())
            updated = repo.update_active_version(saved.id, version_id)
            assert updated is not None
            assert updated.active_version_id == version_id
        finally:
            session.close()

    def test_update_active_version_returns_none_for_missing_dataset(self):
        session = _make_postgres_session()
        try:
            repo = DatasetRepository(session)
            result = repo.update_active_version("no-such-id", "ver-1")
            assert result is None
        finally:
            session.close()

    def test_update_active_version_overwrites_previous(self):
        session = _make_postgres_session()
        try:
            repo = DatasetRepository(session)
            dataset = Dataset(
                id="ds-1",
                project_id="proj-1",
                connection_id="conn-1",
                name="test-dataset",
                active_version_id="old-ver",
            )
            saved = repo.save(dataset)
            assert saved.active_version_id == "old-ver"
            updated = repo.update_active_version("ds-1", "new-ver")
            assert updated.active_version_id == "new-ver"
        finally:
            session.close()

