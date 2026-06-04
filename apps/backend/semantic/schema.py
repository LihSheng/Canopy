import uuid
from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from common.database import Base


class ObjectTypeModel(Base):
    __tablename__ = "semantic_object_types"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    object_type_key: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    plural_name: Mapped[str] = mapped_column(String(255), default="", nullable=False)
    icon: Mapped[str] = mapped_column(String(100), default="", nullable=False)
    groups: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String(50), default="in_progress", nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )

    __table_args__ = (UniqueConstraint("tenant_id", "object_type_key", name="uq_object_type_key_per_tenant"),)


class SemanticMappingModel(Base):
    __tablename__ = "semantic_mappings"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    dataset_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    dataset_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    object_type_id: Mapped[str] = mapped_column(String(36), ForeignKey("semantic_object_types.id"), nullable=False)
    object_type_key: Mapped[str] = mapped_column(String(255), nullable=False)
    properties: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    links: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    source_nodes: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    computed_properties: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    layout_state: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False
    )

    object_type = relationship("ObjectTypeModel")

    __table_args__ = (
        UniqueConstraint("dataset_id", "dataset_version_id", "version_number", name="uq_mapping_version"),
    )
