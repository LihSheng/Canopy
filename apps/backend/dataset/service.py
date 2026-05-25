import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from common.errors import NotFoundError, ValidationError
from connection._shared import storage_root
from connection.materialization import materialize_dataset_version
from connection.preview import build_sheet_profiles
from connection.repository import ConnectionRepository
from dataset.cleaning import clean_source_file
from dataset.domain import Dataset, DatasetStatus, DatasetVersion, DatasetVersionStatus
from dataset.repository import DatasetRepository, DatasetVersionRepository
from run.repository import RunRepository


class DatasetService:
    def __init__(self, repo: DatasetRepository, version_repo: DatasetVersionRepository):
        self._repo = repo
        self._version_repo = version_repo

    def create_dataset(
        self,
        project_id: str,
        connection_id: str,
        name: str,
        source_object_name: str = "",
        sync_mode: str | None = None,
        batch_strategy: str | None = None,
        real_time_strategy: str | None = None,
        cursor_column: str | None = None,
    ) -> Dataset:
        now = datetime.now(UTC)
        dataset = Dataset(
            id=str(uuid.uuid4()),
            project_id=project_id,
            connection_id=connection_id,
            name=name,
            source_object_name=source_object_name,
            status=DatasetStatus.ACTIVE.value,
            sync_mode=sync_mode,
            batch_strategy=batch_strategy,
            real_time_strategy=real_time_strategy,
            cursor_column=cursor_column,
            created_at=now,
        )
        dataset = self._repo.save(dataset)

        connection = ConnectionRepository(self._repo._db).get(connection_id)
        if connection is not None:
            source_file_path = ConnectionRepository(self._repo._db).resolve_static_source_file_path(connection)
            if connection.source_type == "static_file" and source_file_path:
                result = clean_source_file(
                    source_file_path=Path(source_file_path),
                    sheet_name=source_object_name or name,
                    dataset_id=dataset.id,
                )
                version = self._version_repo.save(
                    DatasetVersion(
                        id=str(uuid.uuid4()),
                        dataset_id=dataset.id,
                        run_id=None,
                        version_number=1,
                        status=DatasetVersionStatus.READY.value,
                        row_count=result["row_count"],
                        column_count=result["column_count"],
                        storage_path=result["cleaned_path"],
                        raw_storage_path=result["raw_path"],
                        cleaning_issues=result["cleaning_issues"],
                    ),
                )
                dataset = self._repo.update_active_version(dataset.id, version.id) or dataset

        return dataset

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
            "blocking_reason": (None if active_run_count == 0 else f"Dataset has {active_run_count} active run(s)"),
        }

    def delete_dataset(self, dataset_id: str) -> dict:
        dataset = self._repo.get(dataset_id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        run_repo = RunRepository(self._repo._db)
        active_run_count = run_repo.count_active_by_dataset(dataset_id)
        if active_run_count > 0:
            raise ValidationError(f"Dataset has {active_run_count} active run(s)")

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

    def update_sync_policy(
        self,
        dataset_id: str,
        sync_mode: str | None = None,
        batch_strategy: str | None = None,
        real_time_strategy: str | None = None,
        cursor_column: str | None = None,
        frequency_minutes: int | None = None,
    ) -> Dataset:
        from dataset.domain import BatchStrategy, RealTimeStrategy, SyncMode

        dataset = self._repo.get(dataset_id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        if sync_mode is not None:
            valid_modes = {m.value for m in SyncMode}
            if sync_mode not in valid_modes:
                raise ValidationError(f"Invalid sync_mode: {sync_mode}")
            dataset.sync_mode = sync_mode
        if batch_strategy is not None:
            valid_strategies = {m.value for m in BatchStrategy}
            if batch_strategy not in valid_strategies:
                raise ValidationError(f"Invalid batch_strategy: {batch_strategy}")
            dataset.batch_strategy = batch_strategy
        if real_time_strategy is not None:
            valid_rt_strategies = {m.value for m in RealTimeStrategy}
            if real_time_strategy not in valid_rt_strategies:
                raise ValidationError(f"Invalid real_time_strategy: {real_time_strategy}")
            dataset.real_time_strategy = real_time_strategy
        if cursor_column is not None:
            dataset.cursor_column = cursor_column
            # Changing cursor column resets last_cursor_value
            dataset.last_cursor_value = None

        if frequency_minutes is not None:
            dataset.frequency_minutes = frequency_minutes

        dataset.updated_at = datetime.now(UTC)
        return self._repo.save(dataset)

    def _hydrate_dataset_version(self, dataset: Dataset) -> Dataset:
        if dataset.active_version_id:
            return dataset

        latest_version = self._version_repo.get_latest_by_dataset(dataset.id)
        if latest_version is not None:
            return self._repo.update_active_version(dataset.id, latest_version.id) or dataset

        connection = ConnectionRepository(self._repo._db).get(dataset.connection_id)
        if connection is None:
            return dataset

        source_file_path = ConnectionRepository(self._repo._db).resolve_static_source_file_path(connection)
        if connection.source_type != "static_file" or not source_file_path:
            return dataset

        result = clean_source_file(
            source_file_path=Path(source_file_path),
            sheet_name=dataset.source_object_name or dataset.name,
            dataset_id=dataset.id,
        )
        version_number = 1
        if latest_version is not None:
            version_number = latest_version.version_number + 1

        version = self._version_repo.save(
            DatasetVersion(
                id=str(uuid.uuid4()),
                dataset_id=dataset.id,
                run_id=None,
                version_number=version_number,
                status=DatasetVersionStatus.READY.value,
                row_count=result["row_count"],
                column_count=result["column_count"],
                storage_path=result["cleaned_path"],
                raw_storage_path=result["raw_path"],
                cleaning_issues=result["cleaning_issues"],
            ),
        )
        return self._repo.update_active_version(dataset.id, version.id) or dataset

    def preview_dataset(
        self,
        id: str,
        page: int = 1,
        page_size: int = 100,
        search: str = "",
    ) -> dict:
        dataset = self._repo.get(id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        dataset = self._hydrate_dataset_version(dataset)

        if dataset.active_version_id is None:
            return {
                "columns": [],
                "rows": [],
                "total_row_count": 0,
                "filtered_row_count": 0,
                "page": page,
                "page_size": page_size,
            }

        version = self._version_repo.get_active_version(id, dataset.active_version_id)
        if version is None or not version.storage_path:
            return {
                "columns": [],
                "rows": [],
                "total_row_count": 0,
                "filtered_row_count": 0,
                "page": page,
                "page_size": page_size,
            }

        from dataset.preview_service import read_dataset_preview

        return read_dataset_preview(
            storage_path=version.storage_path,
            page=page,
            page_size=page_size,
            search=search or None,
        )

    def get_lineage(self, id: str) -> dict:
        dataset = self._repo.get(id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        runs = RunRepository(self._repo._db).list_by_dataset(id)
        versions = self._version_repo.list_by_dataset(id)

        connection = ConnectionRepository(self._repo._db).get(dataset.connection_id)

        nodes: list[dict] = []
        edges: list[dict] = []

        if dataset.source_object_name:
            nodes.append({"id": f"source_{id}", "type": "source_object", "label": dataset.source_object_name})

        if connection is not None:
            nodes.append({"id": f"connection_{dataset.connection_id}", "type": "connection", "label": connection.name})

        nodes.append({"id": f"dataset_{id}", "type": "dataset", "label": dataset.name})

        if dataset.source_object_name and connection is not None:
            edges.append({"from": f"source_{id}", "to": f"connection_{dataset.connection_id}", "type": "feeds"})

        if connection is not None:
            edges.append({"from": f"connection_{dataset.connection_id}", "to": f"dataset_{id}", "type": "provides"})

        for v in versions:
            nodes.append({"id": f"version_{v.id}", "type": "version", "label": f"v{v.version_number}"})
            edges.append({"from": f"version_{v.id}", "to": f"dataset_{id}", "type": "belongs_to"})

        for r in runs:
            nodes.append({"id": f"run_{r.id}", "type": "run", "label": r.status})
            edges.append({"from": f"run_{r.id}", "to": f"dataset_{id}", "type": "produces"})

        return {"nodes": nodes, "edges": edges}


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

    def reimport_version(
        self,
        dataset_id: str,
        data_path: str,
        columns: list[str],
        sheet_name: str | None = None,
    ) -> DatasetVersion:
        dataset = self._dataset_repo.get(dataset_id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        existing = self._repo.list_by_dataset(dataset_id)
        next_number = (existing[0].version_number + 1) if existing else 1
        now = datetime.now(UTC)
        resolved_sheet_name = self._resolve_reimport_sheet_name(
            Path(data_path),
            sheet_name,
            dataset.source_object_name or dataset.name,
        )
        storage_path, row_count, column_count = materialize_dataset_version(
            Path(data_path),
            resolved_sheet_name,
            dataset_id,
        )
        new_version = DatasetVersion(
            id=str(uuid.uuid4()),
            dataset_id=dataset_id,
            version_number=next_number,
            status=DatasetVersionStatus.READY.value,
            created_at=now,
            row_count=row_count,
            column_count=column_count,
            storage_path=str(storage_path),
            raw_storage_path=data_path,
            cleaning_issues=[],
        )
        saved = self._repo.save(new_version)
        self._dataset_repo.update_active_version(dataset_id, saved.id)
        return saved

    def _resolve_reimport_sheet_name(
        self,
        data_path: Path,
        requested_sheet_name: str | None,
        default_sheet_name: str,
    ) -> str:
        profiles = build_sheet_profiles(data_path)
        if not profiles:
            return requested_sheet_name or default_sheet_name

        if requested_sheet_name:
            requested_profile = next(
                (profile for profile in profiles if profile["sheet_name"] == requested_sheet_name),
                None,
            )
            if requested_profile and requested_profile.get("data_row_count", 0) > 0:
                return requested_sheet_name

        populated_profile = next(
            (profile for profile in profiles if profile.get("data_row_count", 0) > 0),
            None,
        )
        if populated_profile:
            return str(populated_profile["sheet_name"])

        if requested_sheet_name and any(profile["sheet_name"] == requested_sheet_name for profile in profiles):
            return requested_sheet_name

        return str(profiles[0]["sheet_name"])

    def mark_version_failed(self, version_id: str, reason: str) -> DatasetVersion | None:
        version = self._repo.get(version_id)
        if version is None:
            return None
        version.status = DatasetVersionStatus.FAILED.value
        version.failure_reason = reason
        self._repo.update(version)
        return version
