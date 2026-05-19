import uuid
import shutil
from datetime import UTC, datetime

from common.errors import NotFoundError, ValidationError
from dataset.domain import Dataset, DatasetVersion, DatasetStatus, DatasetVersionStatus
from dataset.repository import DatasetRepository, DatasetVersionRepository
from connection._shared import storage_root
from run.repository import RunRepository


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

    def get_delete_summary(self, dataset_id: str) -> dict:
        dataset = self._repo.get(dataset_id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        run_repo = RunRepository(self._repo._db)
        active_run_count = run_repo.count_active_by_dataset(dataset_id)
        version_count = self._version_repo.count_by_dataset(dataset_id)
        return {
            "dataset_id": dataset_id,
            "version_count": version_count,
            "active_run_count": active_run_count,
            "can_delete": active_run_count == 0,
            "blocking_reason": (
                None
                if active_run_count == 0
                else f"Dataset has {active_run_count} active run(s)"
            ),
        }

    def delete_dataset(self, dataset_id: str) -> dict:
        dataset = self._repo.get(dataset_id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        run_repo = RunRepository(self._repo._db)
        active_run_count = run_repo.count_active_by_dataset(dataset_id)
        if active_run_count > 0:
            raise ValidationError(
                f"Dataset has {active_run_count} active run(s)"
            )

        self._version_repo.delete_by_dataset(dataset_id)
        deleted = self._repo.delete(dataset_id)
        if not deleted:
            raise NotFoundError("Dataset not found")

        dataset_storage_dir = storage_root() / dataset_id
        if dataset_storage_dir.exists():
            shutil.rmtree(dataset_storage_dir)

        return {"deleted": True, "id": dataset_id}

    def get_dataset_health(self, dataset_id: str) -> dict:
        dataset = self._repo.get(dataset_id)
        if dataset is None:
            return {}

        from run.repository import RunRepository
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
            "cleaning_issue_count": len(active_version.cleaning_issues) if active_version else 0,
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

    def get_delete_summary(self, dataset_id: str, version_id: str) -> dict:
        dataset = self._dataset_repo.get(dataset_id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        version = self._repo.get(version_id)
        if version is None or version.dataset_id != dataset_id:
            raise NotFoundError("Dataset version not found")

        is_active_version = dataset.active_version_id == version_id
        return {
            "dataset_id": dataset_id,
            "version_id": version_id,
            "version_number": version.version_number,
            "is_active_version": is_active_version,
            "can_delete": not is_active_version,
            "blocking_reason": "Version is active" if is_active_version else None,
        }

    def delete_version(self, dataset_id: str, version_id: str) -> dict:
        dataset = self._dataset_repo.get(dataset_id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        version = self._repo.get(version_id)
        if version is None or version.dataset_id != dataset_id:
            raise NotFoundError("Dataset version not found")

        if dataset.active_version_id == version_id:
            raise ValidationError("Cannot delete active version")

        deleted = self._repo.delete(version_id)
        if not deleted:
            raise NotFoundError("Dataset version not found")

        return {"deleted": True, "id": version_id}

    def reimport_version(self, dataset_id: str, data_path: str, columns: list[str]) -> DatasetVersion:
        existing = self._repo.list_by_dataset(dataset_id)
        next_number = (existing[0].version_number + 1) if existing else 1
        now = datetime.now(UTC)
        new_version = DatasetVersion(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            version_number=next_number,
            status=DatasetVersionStatus.READY.value,
            created_at=now,
        )
        saved = self._repo.save(new_version)
        self._dataset_repo.update_active_version(dataset_id, saved.id)
        return saved

    def mark_version_failed(self, version_id: str, reason: str) -> DatasetVersion | None:
        version = self._repo.get(version_id)
        if version is None:
            return None
        version.status = DatasetVersionStatus.FAILED.value
        version.failure_reason = reason
        self._repo.update(version)
        return version


