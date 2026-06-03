import asyncio
import logging
import shutil
import uuid
from datetime import UTC, datetime
from pathlib import Path

from common.errors import NotFoundError, ValidationError
from connection._shared import storage_root
from connection.database_adapter import get_adapter
from connection.materialization import materialize_dataset_version
from connection.preview import build_sheet_profiles
from connection.repository import ConnectionRepository
from connection.secret_store import AesGcmSecretStore, decrypt_secret_value
from dataset.domain import Dataset, DatasetStatus, DatasetVersion, DatasetVersionStatus
from dataset.repository import DatasetRepository, DatasetVersionRepository
from run.repository import RunRepository

logger = logging.getLogger(__name__)


class DatasetService:
    def __init__(self, repo: DatasetRepository, version_repo: DatasetVersionRepository):
        self._repo = repo
        self._version_repo = version_repo

    def create_dataset(
        self,
        tenant_id: str,
        project_id: str,
        connection_id: str,
        name: str,
        source_object_name: str = "",
        defer_materialization: bool = False,
        sync_mode: str | None = None,
        batch_strategy: str | None = None,
        real_time_strategy: str | None = None,
        cursor_column: str | None = None,
    ) -> Dataset:
        return asyncio.run(
            self.create_dataset_async(
                tenant_id=tenant_id,
                project_id=project_id,
                connection_id=connection_id,
                name=name,
                source_object_name=source_object_name,
                defer_materialization=defer_materialization,
                sync_mode=sync_mode,
                batch_strategy=batch_strategy,
                real_time_strategy=real_time_strategy,
                cursor_column=cursor_column,
            )
        )

    async def create_dataset_async(
        self,
        tenant_id: str,
        project_id: str,
        connection_id: str,
        name: str,
        source_object_name: str = "",
        defer_materialization: bool = False,
        sync_mode: str | None = None,
        batch_strategy: str | None = None,
        real_time_strategy: str | None = None,
        cursor_column: str | None = None,
    ) -> Dataset:
        now = datetime.now(UTC)
        resolved_source_object_name = source_object_name or name

        if defer_materialization:
            existing = self._repo.get_by_connection_and_source_object_name(
                connection_id=connection_id,
                source_object_name=resolved_source_object_name,
                tenant_id=tenant_id,
            )
            if existing is not None:
                existing.name = name
                existing.sync_mode = sync_mode
                existing.batch_strategy = batch_strategy
                existing.real_time_strategy = real_time_strategy
                existing.cursor_column = cursor_column
                existing.updated_at = now
                return self._repo.save(existing)

        dataset = Dataset(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            project_id=project_id,
            connection_id=connection_id,
            name=name,
            source_object_name=resolved_source_object_name,
            status=(DatasetStatus.PENDING_INITIAL_RUN.value if defer_materialization else DatasetStatus.ACTIVE.value),
            sync_mode=sync_mode,
            batch_strategy=batch_strategy,
            real_time_strategy=real_time_strategy,
            cursor_column=cursor_column,
            created_at=now,
        )
        dataset = self._repo.save(dataset)

        try:
            connection_repo = ConnectionRepository(self._repo._db)
            connection = connection_repo.get(connection_id)
            if connection is not None:
                if defer_materialization and connection.source_type in {"postgresql", "mysql"}:
                    return dataset
                source_file_path = connection_repo.resolve_static_source_file_path(connection)
                if connection.source_type == "static_file" and source_file_path:
                    landing_path, row_count, column_count = materialize_dataset_version(
                        Path(source_file_path),
                        source_object_name or name,
                        dataset.id,
                    )
                    version = self._version_repo.save(
                        DatasetVersion(
                            id=str(uuid.uuid4()),
                            dataset_id=dataset.id,
                            run_id=None,
                            version_number=1,
                            status=DatasetVersionStatus.READY.value,
                            row_count=row_count,
                            column_count=column_count,
                            storage_path=str(landing_path),
                            raw_storage_path=str(source_file_path),
                            cleaning_issues=[],
                        ),
                    )
                    dataset = self._repo.update_active_version(dataset.id, version.id) or dataset
                elif connection.source_type in {"postgresql", "mysql"}:
                    try:
                        version = await self._materialize_database_dataset_version_async(
                            connection=connection,
                            dataset=dataset,
                            source_object_name=source_object_name or name,
                        )
                        dataset = self._repo.update_active_version(dataset.id, version.id) or dataset
                    except Exception:
                        logger.exception(
                            "Failed to materialize dataset version",
                            extra={
                                "dataset_id": dataset.id,
                                "connection_id": connection.id,
                                "source_type": connection.source_type,
                                "source_object_name": source_object_name or name,
                            },
                        )
                        raise
        except Exception:
            logger.exception(
                "Failed during dataset post-save setup",
                extra={
                    "dataset_id": dataset.id,
                    "connection_id": connection_id,
                    "source_type": connection.source_type if connection is not None else None,
                    "source_object_name": source_object_name or name,
                },
            )
            raise

        return dataset

    def update_dataset_name(self, id: str, name: str, tenant_id: str | None = None) -> Dataset:
        import re

        dataset = self._repo.get(id, tenant_id=tenant_id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        stripped = name.strip()
        if not stripped:
            raise ValidationError("Dataset name must not be empty")
        if not re.match(r"^[A-Za-z]", stripped):
            raise ValidationError("Dataset name must start with a letter")
        if not re.match(r"^[A-Za-z][A-Za-z0-9 _-]*$", stripped):
            raise ValidationError(
                "Dataset name contains invalid characters. "
                "Only letters, digits, spaces, hyphens, and underscores are allowed."
            )

        dataset.name = stripped
        dataset.updated_at = datetime.now(UTC)
        return self._repo.save(dataset)

    def get_dataset(self, id: str, tenant_id: str | None = None) -> Dataset | None:
        return self._repo.get(id, tenant_id=tenant_id)

    def list_datasets(self, project_id: str, tenant_id: str | None = None) -> list[Dataset]:
        return self._repo.list_by_project(project_id, tenant_id=tenant_id)

    def list_all_datasets(self, tenant_id: str | None = None) -> list[Dataset]:
        return self._repo.list_all(tenant_id=tenant_id)

    def get_delete_summary(self, dataset_id: str, tenant_id: str | None = None) -> dict:
        dataset = self._repo.get(dataset_id, tenant_id=tenant_id)
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

    def delete_dataset(self, dataset_id: str, tenant_id: str | None = None) -> dict:
        dataset = self._repo.get(dataset_id, tenant_id=tenant_id)
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

    def get_bulk_delete_summary(self, dataset_ids: list[str], tenant_id: str | None = None) -> list[dict]:
        """Return per-dataset delete eligibility summaries for a batch of dataset IDs."""
        if not dataset_ids:
            return []

        run_repo = RunRepository(self._repo._db)
        results: list[dict] = []
        for dataset_id in dataset_ids:
            dataset = self._repo.get(dataset_id, tenant_id=tenant_id)
            if dataset is None:
                results.append(
                    {
                        "dataset_id": dataset_id,
                        "version_count": 0,
                        "active_run_count": 0,
                        "can_delete": False,
                        "blocking_reason": "Dataset not found",
                        "dataset_name": None,
                    }
                )
                continue

            active_run_count = run_repo.count_active_by_dataset(dataset_id)
            version_count = self._version_repo.count_by_dataset(dataset_id)
            can_delete = active_run_count == 0 and dataset is not None
            blocking_reason = (
                None
                if can_delete
                else (f"Dataset has {active_run_count} active run(s)" if active_run_count > 0 else "Dataset not found")
            )
            results.append(
                {
                    "dataset_id": dataset_id,
                    "version_count": version_count,
                    "active_run_count": active_run_count,
                    "can_delete": can_delete,
                    "blocking_reason": blocking_reason,
                    "dataset_name": dataset.name,
                }
            )
        return results

    def bulk_delete_datasets(self, dataset_ids: list[str], tenant_id: str | None = None) -> dict:
        """Delete allowed datasets from the given list. Blocked datasets are skipped.

        Returns a result summary with per-dataset outcomes.
        """
        if not dataset_ids:
            return {"deleted": [], "skipped": [], "total_requested": 0}

        run_repo = RunRepository(self._repo._db)
        deleted: list[dict] = []
        skipped: list[dict] = []

        for dataset_id in dataset_ids:
            dataset = self._repo.get(dataset_id, tenant_id=tenant_id)
            if dataset is None:
                skipped.append(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": None,
                        "reason": "Dataset not found",
                    }
                )
                continue

            active_run_count = run_repo.count_active_by_dataset(dataset_id)
            if active_run_count > 0:
                skipped.append(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset.name,
                        "reason": f"Dataset has {active_run_count} active run(s)",
                    }
                )
                continue

            try:
                self._version_repo.delete_by_dataset(dataset_id)
                self._repo.delete(dataset_id)

                dataset_storage_dir = storage_root() / dataset_id
                if dataset_storage_dir.exists():
                    shutil.rmtree(dataset_storage_dir)

                deleted.append(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset.name,
                    }
                )
            except Exception:
                logger.exception(
                    "Bulk delete failed for dataset",
                    extra={"dataset_id": dataset_id, "tenant_id": tenant_id},
                )
                skipped.append(
                    {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset.name,
                        "reason": "Delete failed unexpectedly",
                    }
                )

        return {
            "deleted": deleted,
            "skipped": skipped,
            "total_requested": len(dataset_ids),
        }

    def get_dataset_health(self, dataset_id: str, tenant_id: str | None = None) -> dict:
        dataset = self._repo.get(dataset_id, tenant_id=tenant_id)
        if dataset is None:
            return {}

        dataset = self._hydrate_dataset_version(dataset)

        from run.repository import RunRepository

        run_repo = RunRepository(self._repo._db)

        active_version = None
        if dataset.active_version_id:
            active_version = self._version_repo.get_active_version(dataset_id, dataset.active_version_id)

        last_run = run_repo.get_latest_by_dataset(dataset_id)
        last_run_status = last_run.status if last_run else None
        last_run_started = last_run.started_at if last_run else None

        # Check schema drift status
        from schema_drift.service import SchemaDriftService

        drift_service = SchemaDriftService(self._repo._db)
        drift_status = drift_service.get_drift_status(dataset_id)

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
            "schema_drift": drift_status,
        }

    def update_sync_policy(
        self,
        dataset_id: str,
        sync_mode: str | None = None,
        batch_strategy: str | None = None,
        real_time_strategy: str | None = None,
        cursor_column: str | None = None,
        frequency_minutes: int | None = None,
        tenant_id: str | None = None,
    ) -> Dataset:
        from dataset.domain import BatchStrategy, RealTimeStrategy, SyncMode

        dataset = self._repo.get(dataset_id, tenant_id=tenant_id)
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

        dataset.updated_at = datetime.now(UTC)
        return self._repo.save(dataset)

    def refresh_dataset_version(self, dataset_id: str, tenant_id: str | None = None) -> DatasetVersion:
        dataset = self._repo.get(dataset_id, tenant_id=tenant_id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        connection_repo = ConnectionRepository(self._repo._db)
        connection = connection_repo.get(dataset.connection_id)
        if connection is None:
            raise NotFoundError("Connection not found")

        if connection.source_type == "static_file":
            raise ValidationError("Static file datasets must be refreshed by uploading a new file")

        if connection.source_type not in {"postgresql", "mysql"}:
            raise ValidationError(f"Unsupported source type for refresh: {connection.source_type}")

        source_object_name = dataset.source_object_name or dataset.name
        version = self._materialize_database_dataset_version(
            connection=connection,
            dataset=dataset,
            source_object_name=source_object_name,
        )
        self._repo.update_active_version(dataset_id, version.id)
        if dataset.status == DatasetStatus.PENDING_INITIAL_RUN.value:
            dataset.status = DatasetStatus.ACTIVE.value
            dataset.updated_at = datetime.now(UTC)
            self._repo.save(dataset)
        return version

    def _hydrate_dataset_version(self, dataset: Dataset) -> Dataset:
        if dataset.status == DatasetStatus.PENDING_INITIAL_RUN.value:
            return dataset
        if dataset.active_version_id:
            return dataset

        latest_version = self._version_repo.get_latest_by_dataset(dataset.id)
        if latest_version is not None:
            return self._repo.update_active_version(dataset.id, latest_version.id) or dataset

        connection_repo = ConnectionRepository(self._repo._db)
        connection = connection_repo.get(dataset.connection_id)
        if connection is None:
            return dataset

        source_file_path = connection_repo.resolve_static_source_file_path(connection)
        if connection.source_type != "static_file" or not source_file_path:
            if connection.source_type in {"postgresql", "mysql"}:
                version = self._materialize_database_dataset_version(
                    connection=connection,
                    dataset=dataset,
                    source_object_name=dataset.source_object_name or dataset.name,
                )
                return self._repo.update_active_version(dataset.id, version.id) or dataset
            return dataset

        landing_path, row_count, column_count = materialize_dataset_version(
            Path(source_file_path),
            dataset.source_object_name or dataset.name,
            dataset.id,
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
                row_count=row_count,
                column_count=column_count,
                storage_path=str(landing_path),
                raw_storage_path=str(source_file_path),
                cleaning_issues=[],
            ),
        )
        return self._repo.update_active_version(dataset.id, version.id) or dataset

    def _materialize_database_dataset_version(
        self,
        connection,
        dataset: Dataset,
        source_object_name: str,
    ) -> DatasetVersion:
        return asyncio.run(
            self._materialize_database_dataset_version_async(
                connection=connection,
                dataset=dataset,
                source_object_name=source_object_name,
            )
        )

    async def _materialize_database_dataset_version_async(
        self,
        connection,
        dataset: Dataset,
        source_object_name: str,
    ) -> DatasetVersion:
        config = self._decrypt_connection_config(connection)
        adapter = get_adapter(connection.source_type)

        storage_path, row_count, column_count = await _materialize_database_dataset_version(
            adapter=adapter,
            config=config,
            table_name=source_object_name,
            dataset_id=dataset.id,
            cursor_column=dataset.cursor_column if dataset.batch_strategy == "incremental_cursor" else None,
            cursor_value=dataset.last_cursor_value if dataset.batch_strategy == "incremental_cursor" else None,
        )

        version_number = self._version_repo.count_by_dataset(dataset.id) + 1
        return self._version_repo.save(
            DatasetVersion(
                id=str(uuid.uuid4()),
                dataset_id=dataset.id,
                run_id=None,
                version_number=version_number,
                status=DatasetVersionStatus.READY.value,
                row_count=row_count,
                column_count=column_count,
                storage_path=str(storage_path),
                raw_storage_path=str(storage_path),
                cleaning_issues=[],
            ),
        )

    def _decrypt_connection_config(self, connection) -> dict:
        config = dict(connection.config_json or {})
        password = config.get("password")
        if password and isinstance(password, str):
            store = AesGcmSecretStore()
            config["password"] = decrypt_secret_value(password, store, allow_legacy_plaintext=True)
        return config

    def preview_dataset(
        self,
        id: str,
        page: int = 1,
        page_size: int = 100,
        search: str = "",
        tenant_id: str | None = None,
    ) -> dict:
        dataset = self._repo.get(id, tenant_id=tenant_id)
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

    def get_lineage(self, id: str, tenant_id: str | None = None) -> dict:
        dataset = self._repo.get(id, tenant_id=tenant_id)
        if dataset is None:
            raise NotFoundError("Dataset not found")

        runs = RunRepository(self._repo._db).list_by_dataset(id)
        versions = self._version_repo.list_by_dataset(id)

        connection = ConnectionRepository(self._repo._db).get(dataset.connection_id)

        nodes: list[dict] = []
        edges: list[dict] = []

        dataset_state = (
            "pending"
            if (dataset.status == DatasetStatus.PENDING_INITIAL_RUN.value or dataset.active_version_id is None)
            else "materialized"
        )

        if dataset.source_object_name:
            nodes.append(
                {
                    "id": f"source_{id}",
                    "type": "source_object",
                    "label": dataset.source_object_name,
                    "state": "materialized",
                }
            )

        if connection is not None:
            nodes.append(
                {
                    "id": f"connection_{dataset.connection_id}",
                    "type": "connection",
                    "label": connection.name,
                    "state": "materialized",
                }
            )

        nodes.append({"id": f"dataset_{id}", "type": "dataset", "label": dataset.name, "state": dataset_state})

        if dataset.source_object_name and connection is not None:
            edges.append({"from": f"source_{id}", "to": f"connection_{dataset.connection_id}", "type": "feeds"})

        if connection is not None:
            edges.append({"from": f"connection_{dataset.connection_id}", "to": f"dataset_{id}", "type": "provides"})

        for v in versions:
            nodes.append(
                {"id": f"version_{v.id}", "type": "version", "label": f"v{v.version_number}", "state": "materialized"}
            )
            edges.append({"from": f"version_{v.id}", "to": f"dataset_{id}", "type": "belongs_to"})

        for r in runs:
            nodes.append({"id": f"run_{r.id}", "type": "run", "label": r.status, "state": "materialized"})
            edges.append({"from": f"run_{r.id}", "to": f"dataset_{id}", "type": "produces"})

        return {"nodes": nodes, "edges": edges}


async def _materialize_database_dataset_version(
    adapter,
    config: dict,
    table_name: str,
    dataset_id: str,
    cursor_column: str | None = None,
    cursor_value: str | None = None,
) -> tuple[Path, int, int]:
    from connection._shared import write_jsonl_version

    all_rows: list[dict] = []
    stream = await adapter.fetch_table(config, table_name, cursor_column, cursor_value)
    async for batch in stream:
        all_rows.extend(batch)

    storage_path = write_jsonl_version(all_rows, dataset_id, table_name)
    row_count = len(all_rows)
    column_count = len(all_rows[0]) if all_rows else 0
    return storage_path, row_count, column_count


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

    def refresh_latest_version(self, dataset_id: str) -> DatasetVersion:
        dataset_service = DatasetService(self._dataset_repo, self._repo)
        return dataset_service.refresh_dataset_version(dataset_id)

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
