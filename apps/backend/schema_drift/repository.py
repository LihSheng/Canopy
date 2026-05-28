"""Repository layer for schema drift persistence."""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from schema_drift.domain import ColumnSchema, SchemaDriftEvent, SchemaSignature
from schema_drift.schema import SchemaDriftEventModel, SchemaSignatureModel


class SchemaSignatureRepository:
    """CRUD for schema_signatures table."""

    def __init__(self, db: Session):
        self._db = db

    def get(self, connection_id: str, source_object_name: str) -> SchemaSignature | None:
        model = (
            self._db.query(SchemaSignatureModel)
            .filter(
                SchemaSignatureModel.connection_id == connection_id,
                SchemaSignatureModel.source_object_name == source_object_name,
            )
            .first()
        )
        return self._to_domain(model) if model else None

    def save(self, sig: SchemaSignature) -> SchemaSignature:
        model = self._get_or_create_model(sig.connection_id, sig.source_object_name)
        model.signature_hash = sig.signature_hash
        model.columns_json = json.dumps([c.to_dict() for c in sig.columns], default=str)
        model.updated_at = datetime.now(UTC)
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def delete(self, connection_id: str, source_object_name: str) -> bool:
        model = (
            self._db.query(SchemaSignatureModel)
            .filter(
                SchemaSignatureModel.connection_id == connection_id,
                SchemaSignatureModel.source_object_name == source_object_name,
            )
            .first()
        )
        if model is None:
            return False
        self._db.delete(model)
        self._db.commit()
        return True

    def _get_or_create_model(self, connection_id: str, source_object_name: str) -> SchemaSignatureModel:
        model = (
            self._db.query(SchemaSignatureModel)
            .filter(
                SchemaSignatureModel.connection_id == connection_id,
                SchemaSignatureModel.source_object_name == source_object_name,
            )
            .first()
        )
        if model is not None:
            return model
        model = SchemaSignatureModel(
            id=str(uuid.uuid4()),
            connection_id=connection_id,
            source_object_name=source_object_name,
            signature_hash="",
            columns_json="[]",
        )
        self._db.add(model)
        self._db.flush()
        return model

    @staticmethod
    def _to_domain(m: SchemaSignatureModel) -> SchemaSignature:
        columns_list: list[dict] = json.loads(m.columns_json) if m.columns_json else []
        columns = [ColumnSchema(**c) for c in columns_list]
        return SchemaSignature(
            connection_id=m.connection_id,
            source_object_name=m.source_object_name,
            columns=columns,
            signature_hash=m.signature_hash,
            created_at=m.created_at,
        )


class SchemaDriftEventRepository:
    """CRUD for schema_drift_events table."""

    def __init__(self, db: Session):
        self._db = db

    def save(self, event: SchemaDriftEvent) -> SchemaDriftEvent:
        model = SchemaDriftEventModel(
            id=str(uuid.uuid4()),
            connection_id=event.connection_id,
            source_object_name=event.source_object_name,
            dataset_id=event.dataset_id,
            drift_type=event.drift_type,
            before_hash=event.before_hash,
            after_hash=event.after_hash,
            delta_json=event.delta.to_dict() if event.delta else {},
            is_breaking=event.delta.is_breaking if event.delta else False,
            detected_by=event.detected_by,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return event  # return domain object, not model

    def list_by_dataset(self, dataset_id: str, limit: int = 20) -> list[dict[str, Any]]:
        models = (
            self._db.query(SchemaDriftEventModel)
            .filter(SchemaDriftEventModel.dataset_id == dataset_id)
            .order_by(SchemaDriftEventModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._model_to_dict(m) for m in models]

    def list_by_connection(self, connection_id: str, limit: int = 50) -> list[dict[str, Any]]:
        models = (
            self._db.query(SchemaDriftEventModel)
            .filter(SchemaDriftEventModel.connection_id == connection_id)
            .order_by(SchemaDriftEventModel.created_at.desc())
            .limit(limit)
            .all()
        )
        return [self._model_to_dict(m) for m in models]

    def get_latest_by_source_object(self, connection_id: str, source_object_name: str) -> dict[str, Any] | None:
        model = (
            self._db.query(SchemaDriftEventModel)
            .filter(
                SchemaDriftEventModel.connection_id == connection_id,
                SchemaDriftEventModel.source_object_name == source_object_name,
            )
            .order_by(SchemaDriftEventModel.created_at.desc())
            .first()
        )
        return self._model_to_dict(model) if model else None

    @staticmethod
    def _model_to_dict(m: SchemaDriftEventModel) -> dict[str, Any]:
        return {
            "id": m.id,
            "connection_id": m.connection_id,
            "source_object_name": m.source_object_name,
            "dataset_id": m.dataset_id,
            "drift_type": m.drift_type,
            "before_hash": m.before_hash,
            "after_hash": m.after_hash,
            "delta": m.delta_json,
            "is_breaking": m.is_breaking,
            "detected_by": m.detected_by,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
