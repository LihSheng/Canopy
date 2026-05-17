import uuid
from datetime import UTC, datetime

from v4.dataset.domain import Dataset, DatasetVersion, DatasetStatus, DatasetVersionStatus
from v4.dataset.repository import DatasetRepository, DatasetVersionRepository


class DatasetService:
    def __init__(self, repo: DatasetRepository, version_repo: DatasetVersionRepository):
        self._repo = repo
        self._version_repo = version_repo

    def create_dataset(self, project_id: str, connection_id: str, name: str, source_object_name: str = "") -> Dataset:
        now = datetime.now(UTC)
        dataset = Dataset(
            id=str(uuid.uuid4()),
            project_id=project_id,
            connection_id=connection_id,
            name=name,
            source_object_name=source_object_name,
            status=DatasetStatus.ACTIVE.value,
            created_at=now,
        )
        return self._repo.save(dataset)

    def get_dataset(self, id: str) -> Dataset | None:
        return self._repo.get(id)

    def list_datasets(self, project_id: str) -> list[Dataset]:
        return self._repo.list_by_project(project_id)

    def list_all_datasets(self) -> list[Dataset]:
        return self._repo.list_all()

    def get_dataset_health(self, dataset_id: str) -> dict:
        dataset = self._repo.get(dataset_id)
        if dataset is None:
            return {}

        from v4.run.repository import RunRepository
        run_repo = RunRepository(self._repo._db)

        active_version = None
        if dataset.active_version_id:
            active_version = self._version_repo.get_active_version(dataset_id, dataset.active_version_id)

        last_run = run_repo.get_latest_by_dataset(dataset_id)
        last_run_status = last_run.status if last_run else None
        last_run_started = last_run.started_at if last_run else None

        return {
            "dataset_id": dataset_id,
            "row_count": active_version.row_count if active_version else 0,
            "column_count": active_version.column_count if active_version else 0,
            "warning_count": last_run.warning_count if last_run else 0,
            "missing_required_mappings": False,
            "last_run_status": last_run_status,
            "last_published_version": active_version.version_number if active_version else None,
            "freshness_at": last_run_started,
        }


class DatasetVersionService:
    def __init__(self, repo: DatasetVersionRepository, dataset_repo: DatasetRepository):
        self._repo = repo
        self._dataset_repo = dataset_repo

    def create_version(self, dataset_id: str, run_id: str | None = None) -> DatasetVersion:
        existing = self._repo.list_by_dataset(dataset_id)
        next_number = (existing[0].version_number + 1) if existing else 1
        now = datetime.now(UTC)
        version = DatasetVersion(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            run_id=run_id,
            version_number=next_number,
            status=DatasetVersionStatus.PENDING.value,
            created_at=now,
        )
        saved = self._repo.save(version)
        return saved

    def list_versions(self, dataset_id: str) -> list[DatasetVersion]:
        return self._repo.list_by_dataset(dataset_id)

    def get_version(self, id: str) -> DatasetVersion | None:
        return self._repo.get(id)
