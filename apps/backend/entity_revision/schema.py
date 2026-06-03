"""SQLAlchemy ORM models for entity_revisions and entity_revision_dependencies."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import (
    JSON,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class EntityRevisionModel(Base):
    __tablename__ = "entity_revisions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("semantic_object_types.id"), nullable=False, index=True
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        comment="draft | published | archived",
    )
    forked_from_revision_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    properties: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    links: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    source_nodes: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    computed_properties: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    layout_state: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    lock_holder_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    __table_args__ = (UniqueConstraint("entity_id", "revision_number", name="uq_entity_revision_number"),)


class EntityRevisionDependencyModel(Base):
    __tablename__ = "entity_revision_dependencies"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    revision_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("entity_revisions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dependency_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        comment="dataset | dataset_version",
    )
    dependency_id: Mapped[str] = mapped_column(String(36), nullable=False)

    __table_args__ = (
        UniqueConstraint("revision_id", "dependency_type", "dependency_id", name="uq_revision_dependency"),
    )
