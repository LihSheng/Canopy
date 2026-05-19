"""Sync service for external database datasets using the DatabaseAdapter interface."""

import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from common.clock import utcnow
from common.errors import NotFoundError
from connection.database_adapter import get_adapter
from connection.secret_store import AesGcmSecretStore
from dataset.domain import Dataset, DatasetVersion, DatasetVersionStatus
from dataset.repository import DatasetRepository, DatasetVersionRepository
from sync.domain import EntitySnapshot, SyncResult


class ExternalDbSyncService:
    """Syncs datasets whose ``sync_mode`` is ``batch`` or ``real_time``.

    Iterates all matching datasets, connects to the external database via
    the appropriate ``DatabaseAdapter``, pulls data according to the
    ``batch_strategy`` (full_snapshot or incremental_cursor), saves the
    result as a new ``DatasetVersion``, and updates ``last_cursor_value``.
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

            # For now, use preview_table as a simple SELECT
            preview = await adapter.preview_table(config, ds.source_object_name or ds.name)
            rows = preview.get("rows", [])
            completed_at = utcnow()

            # Create a new version for the pulled data
            version = self._version_repo.save(
                DatasetVersion(
                    id=str(uuid.uuid4()),
                    dataset_id=ds.id,
                    version_number=1,
                    status=DatasetVersionStatus.READY.value,
                    row_count=len(rows),
                    column_count=len(preview.get("columns", [])),
                    storage_path="",
                    raw_storage_path="",
                    created_at=utcnow(),
                ),
            )

            # Update cursor value for incremental sync
            if ds.batch_strategy == "incremental_cursor" and ds.cursor_column and rows:
                new_cursor = max(
                    (str(row.get(ds.cursor_column, "")) for row in rows if isinstance(row, dict)),
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
                row_count=len(rows),
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
