"""SQLAlchemy ORM model for entity_materialized_rows."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class EntityMaterializedRowModel(Base):
    __tablename__ = "entity_materialized_rows"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("semantic_object_types.id"),
        nullable=False,
        index=True,
    )
    revision_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("entity_revisions.id"),
        nullable=False,
        index=True,
    )
    row_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    row_data: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    is_tombstone: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
    )
    materialized_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
