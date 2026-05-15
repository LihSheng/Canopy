import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class RefreshJobModel(Base):
    __tablename__ = "refresh_jobs"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    current_stage: Mapped[str | None] = mapped_column(String(32), nullable=True)
    snapshot_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    trigger_type: Mapped[str] = mapped_column(String(16), nullable=False, default="manual")
    requested_by_user_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class DataSnapshotModel(Base):
    __tablename__ = "data_snapshots"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    refresh_job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("refresh_jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="current")
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
