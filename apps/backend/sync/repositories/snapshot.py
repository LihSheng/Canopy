import json
import uuid
from typing import Any

from sqlalchemy.orm import Session

from sync.schema import SourceSnapshotModel, SourceSnapshotRowModel


class SnapshotRepository:
    def __init__(self, db: Session):
        self._db = db

    def save_snapshot(self, snapshot_model: SourceSnapshotModel) -> SourceSnapshotModel:
        self._db.add(snapshot_model)
        self._db.commit()
        self._db.refresh(snapshot_model)
        return snapshot_model

    def save_rows(
        self,
        snapshot_model_id: str,
        rows: list[Any],
    ) -> list[SourceSnapshotRowModel]:
        row_models = [
            SourceSnapshotRowModel(
                id=str(uuid.uuid4()),
                snapshot_id=snapshot_model_id,
                source_key=self._extract_source_key(row),
                entity_data=json.dumps(self._row_to_dict(row), default=str),
            )
            for row in rows
        ]
        self._db.add_all(row_models)
        self._db.commit()
        return row_models

    @staticmethod
    def _extract_source_key(row: Any) -> str:
        if hasattr(row, "source_key"):
            return str(row.source_key)
        if isinstance(row, dict):
            return str(row.get("source_key", ""))
        return "unknown"

    @staticmethod
    def _row_to_dict(row: Any) -> dict[str, Any]:
        if hasattr(row, "__dataclass_fields__"):
            from dataclasses import asdict  # type: ignore[attr-defined]

            return asdict(row)
        if isinstance(row, dict):
            return row
        return {"value": str(row)}
