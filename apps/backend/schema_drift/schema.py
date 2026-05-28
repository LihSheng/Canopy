"""SQLAlchemy models for schema drift tracking."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class SchemaSignatureModel(Base):
    """Current known schema signature per source object (connection_id + source_object_name)."""

    __tablename__ = "schema_signatures"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_object_name: Mapped[str] = mapped_column(String(255), nullable=False)
    signature_hash: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    columns_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )


class SchemaDriftEventModel(Base):
    """Immutable history of schema drift detection events."""

    __tablename__ = "schema_drift_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    connection_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_object_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dataset_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    drift_type: Mapped[str] = mapped_column(String(50), default="detected", nullable=False)
    before_hash: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    after_hash: Mapped[str] = mapped_column(String(64), default="", nullable=False)
    delta_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    is_breaking: Mapped[bool] = mapped_column(default=False, nullable=False)
    detected_by: Mapped[str] = mapped_column(String(50), default="discovery", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
