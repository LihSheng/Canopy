from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class UploadModel(Base):
    __tablename__ = "uploads"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    file_name: Mapped[str] = mapped_column(
        String(255),
        default="",
        server_default=text("''"),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default=text("0"),
        nullable=False,
    )
    mime_type: Mapped[str] = mapped_column(
        String(255),
        default="",
        server_default=text("''"),
        nullable=False,
    )
    storage_path: Mapped[str] = mapped_column(
        String(500),
        default="",
        server_default=text("''"),
        nullable=False,
    )
    checksum: Mapped[str] = mapped_column(
        String(128),
        default="",
        server_default=text("''"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="uploaded",
        server_default=text("'uploaded'"),
        nullable=False,
    )
    source_profile: Mapped[str] = mapped_column(
        String(100),
        default="",
        server_default=text("''"),
        nullable=False,
    )
    dataset_type: Mapped[str] = mapped_column(
        String(100),
        default="",
        server_default=text("''"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        server_default=text("CURRENT_TIMESTAMP"),
        nullable=False,
    )


class MappingDecisionModel(Base):
    __tablename__ = "mapping_decisions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    upload_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_column_name: Mapped[str] = mapped_column(String(255), nullable=False)
    target_field_name: Mapped[str] = mapped_column(String(255), nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    overridden_by_user: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class TemplateFamilyModel(Base):
    __tablename__ = "template_families"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    dataset_type: Mapped[str] = mapped_column(String(100), nullable=False)
    source_profile: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="", nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class TemplateVersionModel(Base):
    __tablename__ = "template_versions"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    template_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    spec_json: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class CleaningPipelineModel(Base):
    __tablename__ = "cleaning_pipelines"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    upload_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="draft", nullable=False)
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class CleaningStepModel(Base):
    __tablename__ = "cleaning_steps"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    pipeline_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    step_type: Mapped[str] = mapped_column(String(100), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    parameters: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class CleanedSnapshotModel(Base):
    __tablename__ = "cleaned_snapshots"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    upload_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    template_version_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(50), default="completed", nullable=False)
    row_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warning_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    warnings: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), default="", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class LineageNodeModel(Base):
    __tablename__ = "lineage_nodes"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    upload_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class LineageEdgeModel(Base):
    __tablename__ = "lineage_edges"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(50), primary_key=True)
    upload_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    from_node_id: Mapped[str] = mapped_column(String(50), nullable=False)
    to_node_id: Mapped[str] = mapped_column(String(50), nullable=False)
    edge_type: Mapped[str] = mapped_column(String(50), nullable=False)
    metadata_json: Mapped[dict] = mapped_column("metadata", JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class WorkflowStateModel(Base):
    __tablename__ = "workflow_state"
    __table_args__ = {"extend_existing": True}

    upload_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    status: Mapped[str] = mapped_column(String(50), default="started", nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    cleaned_snapshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    publish_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    completed_steps: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    current_step: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)


class PublishRecordModel(Base):
    __tablename__ = "publish_records"
    __table_args__ = {"extend_existing": True}

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    upload_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    cleaned_snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False)
    template_version_id: Mapped[str] = mapped_column(String(36), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    validation_errors: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    validation_warnings: Mapped[dict] = mapped_column(JSON, default=list, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    published_by: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
