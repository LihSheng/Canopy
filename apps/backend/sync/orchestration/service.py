import uuid
from collections.abc import Sequence
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from common.clock import utcnow
from sync.domain import EntitySnapshot, SourceReader, SyncResult
from sync.schema import SourceSnapshotModel


class SyncOrchestrator:
    def __init__(
        self,
        readers: Sequence[SourceReader[Any]],
        app_db: Session,
        source_db: Session,
    ):
        self._readers = list(readers)
        self._app_db = app_db
        self._source_db = source_db

    def run(self) -> SyncResult:
        snapshot_id = str(uuid.uuid4())
        started_at = utcnow()

        entity_snapshots: list[EntitySnapshot] = []
        errors: list[str] = []

        for reader in self._readers:
            snap = self._extract_one(reader, started_at)
            entity_snapshots.append(snap)
            if snap.status == "failed":
                errors.append(f"{reader.entity_type}: {snap.error_message}")

        completed_at = utcnow()

        if len(errors) == 0:
            status = "completed"
        elif len(errors) == len(self._readers):
            status = "failed"
        else:
            status = "partial"

        result = SyncResult(
            snapshot_id=snapshot_id,
            status=status,
            started_at=started_at,
            completed_at=completed_at,
            snapshots=entity_snapshots,
            error_message="; ".join(errors) if errors else None,
        )
        self._persist_snapshots(snapshot_id, entity_snapshots)
        self._app_db.commit()
        return result

    def _extract_one(
        self,
        reader: SourceReader[Any],
        started_at: datetime,
    ) -> EntitySnapshot:
        try:
            rows = reader.read(self._source_db)
            completed_at = utcnow()
            return EntitySnapshot(
                entity_type=reader.entity_type,
                status="completed",
                started_at=started_at,
                completed_at=completed_at,
                row_count=len(rows),
                rows=rows,
            )
        except Exception as exc:
            completed_at = utcnow()
            return EntitySnapshot(
                entity_type=reader.entity_type,
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                row_count=0,
                error_message=str(exc),
            )

    def _persist_snapshots(self, snapshot_id: str, snapshots: list[EntitySnapshot]) -> None:
        from sync.repositories.snapshot import SnapshotRepository

        repo = SnapshotRepository(self._app_db)
        for snap in snapshots:
            model = SourceSnapshotModel(
                id=str(uuid.uuid4()),
                entity_type=snap.entity_type,
                status=snap.status,
                started_at=snap.started_at,
                completed_at=snap.completed_at,
                row_count=snap.row_count,
                error_message=snap.error_message,
                snapshot_id=snapshot_id,
            )
            saved = repo.save_snapshot(model)
            if snap.rows:
                repo.save_rows(saved.id, snap.rows)
