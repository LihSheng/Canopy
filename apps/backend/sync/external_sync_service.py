"""Sync service for external database datasets using the DatabaseAdapter interface."""

import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

from sqlalchemy.orm import Session

from common.clock import utcnow
from common.errors import NotFoundError
from connection._shared import slugify, storage_root
from connection.database_adapter import get_adapter
from connection.secret_store import AesGcmSecretStore
from dataset.domain import Dataset, DatasetVersion, DatasetVersionStatus
from dataset.repository import DatasetRepository, DatasetVersionRepository
from sync.domain import EntitySnapshot, SyncResult


class ExternalDbSyncService:
    """Syncs datasets whose ``sync_mode`` is ``batch`` or ``real_time``.

    Iterates all matching datasets, connects to the external database via
    the appropriate ``DatabaseAdapter``, streams data via ``fetch_table``,
    persists the rows to a JSONL file on local disk / object storage,
    creates a new ``DatasetVersion`` pointing to that file, and updates
    ``last_cursor_value`` for incremental cursor mode.
    """

    def __init__(self, app_db: Session):
        self._app_db = app_db
        self._dataset_repo = DatasetRepository(app_db)
        self._version_repo = DatasetVersionRepository(app_db)
        self._secret_store = AesGcmSecretStore()

    async def run_async(self) -> SyncResult:
        """Async entry point — call via ``asyncio.run()`` or from an async context."""
        snapshot_id = str(uuid.uuid4())
        started_at = utcnow()
        datasets = self._dataset_repo.list_all()

        snapshots: list[EntitySnapshot] = []
        errors: list[str] = []

        for ds in datasets:
            if ds.sync_mode not in ("batch", "real_time"):
                continue

            snap = await self._sync_one(ds, started_at)
            snapshots.append(snap)
            if snap.status == "failed":
                errors.append(f"{ds.name}: {snap.error_message}")

        completed_at = utcnow()

        if not snapshots:
            status = "completed"
        elif len(errors) == 0:
            status = "completed"
        elif len(errors) == len(snapshots):
            status = "failed"
        else:
            status = "partial"

        return SyncResult(
            snapshot_id=snapshot_id,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            snapshots=snapshots,
            error_message="; ".join(errors) if errors else None,
        )

    async def _sync_one(self, ds: Dataset, started_at: datetime) -> EntitySnapshot:
        try:
            from connection.repository import ConnectionRepository

            conn_repo = ConnectionRepository(self._app_db)
            conn = conn_repo.get(ds.connection_id)
            if conn is None:
                raise NotFoundError(f"Connection {ds.connection_id} not found")

            config = dict(conn.config_json or {})
            if "password" in config:
                config["password"] = self._secret_store.decrypt(config["password"])

            adapter = get_adapter(conn.source_type)
            table_name = ds.source_object_name or ds.name

            # Determine cursor filter for incremental sync
            cursor_column = ds.cursor_column if ds.batch_strategy == "incremental_cursor" else None
            cursor_value = ds.last_cursor_value if cursor_column else None

            # Stream all rows via the dedicated batch method
            all_rows: list[dict] = []
            async for batch in adapter.fetch_table(config, table_name, cursor_column, cursor_value):
                all_rows.extend(batch)

            completed_at = utcnow()

            # Persist rows to JSONL storage
            storage_path = self._write_rows_to_storage(ds.id, table_name, all_rows)

            # Create a new version pointing to the persisted data
            version = self._version_repo.save(
                DatasetVersion(
                    id=str(uuid.uuid4()),
                    dataset_id=ds.id,
                    version_number=1,
                    status=DatasetVersionStatus.READY.value,
                    row_count=len(all_rows),
                    column_count=len(all_rows[0]) if all_rows else 0,
                    storage_path=str(storage_path),
                    raw_storage_path=str(storage_path),
                    created_at=utcnow(),
                ),
            )

            # Update cursor value for incremental sync
            if cursor_column and cursor_value is not None and all_rows:
                new_cursor = max(
                    (
                        str(row.get(cursor_column, ""))
                        for row in all_rows
                        if isinstance(row, dict)
                    ),
                    default=ds.last_cursor_value,
                )
                if new_cursor != ds.last_cursor_value:
                    ds.last_cursor_value = new_cursor
                    self._dataset_repo.save(ds)

            # Mark the dataset's active version
            self._dataset_repo.update_active_version(ds.id, version.id)

            return EntitySnapshot(
                entity_type=ds.name,
                status="completed",
                started_at=started_at,
                completed_at=completed_at,
                row_count=len(all_rows),
            )

        except Exception as exc:
            completed_at = utcnow()
            return EntitySnapshot(
                entity_type=ds.name,
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                row_count=0,
                error_message=str(exc),
            )

    @staticmethod
    def _write_rows_to_storage(dataset_id: str, table_name: str, rows: list[dict]) -> Path:
        """Write rows to a JSONL file and return the path."""
        version_dir = storage_root() / dataset_id
        version_dir.mkdir(parents=True, exist_ok=True)
        file_path = version_dir / f"{slugify(table_name)}.jsonl"
        with open(file_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, default=str))
                f.write("\n")
        return file_path
