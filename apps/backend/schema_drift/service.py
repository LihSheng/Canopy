"""Service for schema drift detection, blocking, and clearing."""

import logging
from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from common.errors import NotFoundError, ValidationError
from control_plane.audit_service import AuditService
from dataset.domain import Dataset, DatasetStatus
from dataset.repository import DatasetRepository
from schema_drift.domain import ColumnSchema, SchemaDriftEvent, SchemaSignature, compute_drift
from schema_drift.repository import SchemaDriftEventRepository, SchemaSignatureRepository

logger = logging.getLogger(__name__)

# Audit event types
AUDIT_SCHEMA_DRIFT_DETECTED = "schema_drift.detected"
AUDIT_SCHEMA_DRIFT_BLOCKED = "schema_drift.blocked_dataset"
AUDIT_SCHEMA_DRIFT_CLEARED = "schema_drift.cleared"


class SchemaDriftService:
    """Detects, records, and manages schema drift."""

    def __init__(
        self,
        db: Session,
        sig_repo: SchemaSignatureRepository | None = None,
        event_repo: SchemaDriftEventRepository | None = None,
        dataset_repo: DatasetRepository | None = None,
        audit: AuditService | None = None,
    ):
        self._db = db
        self._sig_repo = sig_repo or SchemaSignatureRepository(db)
        self._event_repo = event_repo or SchemaDriftEventRepository(db)
        self._dataset_repo = dataset_repo or DatasetRepository(db)
        self._audit = audit

    # ── Public API ────────────────────────────────────────────────────

    def check_and_record_drift(
        self,
        connection_id: str,
        source_object_name: str,
        raw_columns: list[dict],
        detected_by: str = "discovery",
        dataset_id: str | None = None,
    ) -> dict[str, Any]:
        """Compare current columns to stored signature and record drift if changed.

        Returns a result dict with:
            - drift_detected: bool
            - is_breaking: bool
            - event: dict | None — the recorded event if drift was detected
            - signature_hash: str — the current (after) hash
        """
        # Normalize incoming columns
        current_columns = self._normalize_raw_columns(raw_columns)
        current_sig = SchemaSignature(
            connection_id=connection_id,
            source_object_name=source_object_name,
            columns=current_columns,
        )
        current_hash = current_sig.compute_hash()

        # Get stored signature
        stored = self._sig_repo.get(connection_id, source_object_name)

        # No stored signature → first discovery, just save baseline
        if stored is None or not stored.signature_hash:
            self._sig_repo.save(current_sig)
            return {
                "drift_detected": False,
                "is_breaking": False,
                "event": None,
                "signature_hash": current_hash,
            }

        # Same hash → no drift
        if stored.signature_hash == current_hash:
            return {
                "drift_detected": False,
                "is_breaking": False,
                "event": None,
                "signature_hash": current_hash,
            }

        # Diff detected — compute delta
        delta = compute_drift(stored.columns, current_columns)

        # Record event
        event = SchemaDriftEvent(
            connection_id=connection_id,
            source_object_name=source_object_name,
            dataset_id=dataset_id,
            drift_type="detected",
            before_hash=stored.signature_hash,
            after_hash=current_hash,
            before_columns=stored.columns,
            after_columns=current_columns,
            delta=delta,
            detected_by=detected_by,
        )
        self._event_repo.save(event)
        self._sig_repo.save(current_sig)

        # Audit: drift detected
        self._record_audit(
            event_type=AUDIT_SCHEMA_DRIFT_DETECTED,
            payload={
                "connection_id": connection_id,
                "source_object_name": source_object_name,
                "dataset_id": dataset_id,
                "is_breaking": delta.is_breaking,
                "delta": delta.to_dict(),
            },
        )

        # If breaking, block affected datasets
        if delta.is_breaking:
            self._block_datasets_for_source(connection_id, source_object_name, dataset_id)

        return {
            "drift_detected": True,
            "is_breaking": delta.is_breaking,
            "event": event.to_dict(),
            "signature_hash": current_hash,
        }

    def clear_block(
        self,
        dataset_id: str,
        actor_user_id: str,
    ) -> Dataset:
        """Manually clear a schema drift block on a dataset.

        Resets status from ``blocked_schema_drift`` to ``active``.
        """
        dataset = self._dataset_repo.get(dataset_id)
        if dataset is None:
            raise NotFoundError("Dataset not found")
        if dataset.status != DatasetStatus.BLOCKED_SCHEMA_DRIFT.value:
            raise ValidationError(f"Dataset status is '{dataset.status}', not 'blocked_schema_drift'")

        dataset.status = DatasetStatus.ACTIVE.value
        dataset.updated_at = datetime.now(UTC)
        saved = self._dataset_repo.save(dataset)

        # Audit: cleared
        self._record_audit(
            event_type=AUDIT_SCHEMA_DRIFT_CLEARED,
            actor_user_id=actor_user_id,
            payload={
                "dataset_id": dataset_id,
                "connection_id": dataset.connection_id,
                "source_object_name": dataset.source_object_name,
            },
        )

        return saved

    def get_drift_status(self, dataset_id: str) -> dict[str, Any]:
        """Return drift status info for a dataset's health endpoint."""
        dataset = self._dataset_repo.get(dataset_id)
        if dataset is None:
            return {}

        latest_event = self._event_repo.get_latest_by_source_object(
            dataset.connection_id, dataset.source_object_name or dataset.name
        )

        if latest_event is None:
            return {
                "drift_detected": False,
                "is_blocked": dataset.status == DatasetStatus.BLOCKED_SCHEMA_DRIFT.value,
                "last_drift_at": None,
                "last_drift_is_breaking": None,
            }

        return {
            "drift_detected": True,
            "is_blocked": dataset.status == DatasetStatus.BLOCKED_SCHEMA_DRIFT.value,
            "last_drift_at": latest_event["created_at"],
            "last_drift_is_breaking": latest_event["is_breaking"],
        }

    def list_drift_events(self, dataset_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """List recent drift events for a dataset."""
        return self._event_repo.list_by_dataset(dataset_id, limit=limit)

    # ── Internal helpers ──────────────────────────────────────────────

    def _block_datasets_for_source(
        self,
        connection_id: str,
        source_object_name: str,
        specific_dataset_id: str | None = None,
    ) -> None:
        """Set all datasets referencing this source object to blocked_schema_drift."""
        if specific_dataset_id:
            datasets_to_block = [specific_dataset_id]
        else:
            all_datasets = self._dataset_repo.list_all()
            datasets_to_block = [
                d.id
                for d in all_datasets
                if d.connection_id == connection_id
                and d.source_object_name == source_object_name
                and d.status not in (DatasetStatus.INACTIVE.value,)
            ]

        for ds_id in datasets_to_block:
            ds = self._dataset_repo.get(ds_id)
            if ds is None or ds.status == DatasetStatus.BLOCKED_SCHEMA_DRIFT.value:
                continue
            ds.status = DatasetStatus.BLOCKED_SCHEMA_DRIFT.value
            ds.updated_at = datetime.now(UTC)
            self._dataset_repo.save(ds)

            self._record_audit(
                event_type=AUDIT_SCHEMA_DRIFT_BLOCKED,
                payload={
                    "dataset_id": ds_id,
                    "connection_id": connection_id,
                    "source_object_name": source_object_name,
                },
            )

    def _normalize_raw_columns(self, raw_columns: list[dict]) -> list[ColumnSchema]:
        """Convert raw adapter column dicts to normalized ColumnSchema list."""
        result: list[ColumnSchema] = []
        for col in raw_columns:
            name = col.get("name", "")
            data_type = col.get("data_type", "unknown")
            nullable = col.get("nullable", True)
            result.append(
                ColumnSchema.from_raw(
                    name=name,
                    data_type=data_type,
                    nullable=nullable,
                    char_max_length=col.get("char_max_length"),
                    numeric_precision=col.get("numeric_precision"),
                    numeric_scale=col.get("numeric_scale"),
                    datetime_precision=col.get("datetime_precision"),
                )
            )
        return result

    def _record_audit(
        self,
        event_type: str,
        payload: dict,
        actor_user_id: str | None = None,
    ) -> None:
        if self._audit is None:
            return
        self._audit.record_event(
            tenant_id=None,
            actor_user_id=actor_user_id or "system",
            event_type=event_type,
            payload=payload,
        )
