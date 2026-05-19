import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from common.database import Base
from dataset.domain import Dataset, DatasetVersion, DatasetStatus, DatasetVersionStatus
from dataset.repository import DatasetRepository, DatasetVersionRepository
from dataset.service import DatasetVersionService

@pytest.fixture(autouse=True)
def _setup_db():
    yield

def _make_sqlite_session():
    engine = create_engine("sqlite:///", connect_args={"check_same_thread": False})
    import dataset.schema  # noqa: F401
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()

class TestDatasetReimportService:
    def test_reimport_valid_data_creates_new_active_version(self):
        # Setup: Existing dataset with v1 active
        session = _make_sqlite_session()
        try:
            version_repo = DatasetVersionRepository(session)
            dataset_repo = DatasetRepository(session)
            service = DatasetVersionService(version_repo, dataset_repo)
            
            ds_id = str(uuid.uuid4())
            dataset = Dataset(id=ds_id, project_id="p1", connection_id="c1", name="test", status=DatasetStatus.ACTIVE.value)
            dataset_repo.save(dataset)
            
            v1 = DatasetVersion(id=str(uuid.uuid4()), dataset_id=ds_id, version_number=1, status=DatasetVersionStatus.READY.value)
            version_repo.save(v1)
            dataset_repo.update_active_version(ds_id, v1.id)
            
            # Action: Reimport
            # (Stubbing the ingestion/validation logic for now as it's not yet implemented)
            # We'll just test the service method existence and basic behavior
            new_version = service.reimport_version(ds_id, data_path="/tmp/data.csv", columns=["A", "B", "C"])
            
            # Assert
            assert new_version.version_number == 2
            assert new_version.status == DatasetVersionStatus.READY.value
            
            updated_dataset = dataset_repo.get(ds_id)
            assert updated_dataset.active_version_id == new_version.id
            
        finally:
            session.close()

    def test_mark_version_failed_sets_status_and_reason(self):
        session = _make_sqlite_session()
        try:
            version_repo = DatasetVersionRepository(session)
            dataset_repo = DatasetRepository(session)
            service = DatasetVersionService(version_repo, dataset_repo)

            version = DatasetVersion(
                id=str(uuid.uuid4()),
                dataset_id=str(uuid.uuid4()),
                version_number=1,
                status=DatasetVersionStatus.PENDING.value,
            )
            version_repo.save(version)

            result = service.mark_version_failed(version.id, "Schema mismatch: missing column A")
            assert result is not None
            assert result.status == DatasetVersionStatus.FAILED.value
            assert result.failure_reason == "Schema mismatch: missing column A"
        finally:
            session.close()

    def test_mark_version_failed_returns_none_for_missing(self):
        session = _make_sqlite_session()
        try:
            version_repo = DatasetVersionRepository(session)
            dataset_repo = DatasetRepository(session)
            service = DatasetVersionService(version_repo, dataset_repo)

            result = service.mark_version_failed("nonexistent-id", "reason")
            assert result is None
        finally:
            session.close()
