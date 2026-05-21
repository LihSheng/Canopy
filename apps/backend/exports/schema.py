import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class ExportJobModel(Base):
    __tablename__ = "export_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    status: Mapped[str] = mapped_column(String(16), nullable=False, default="pending")
    preset_name: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    time_range: Mapped[str] = mapped_column(String(32), nullable=False, default="this_month")
    snapshot_timestamp: Mapped[str | None] = mapped_column(String(64), nullable=True)
    requested_by_user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True, index=True
    )
    include_departments: Mapped[bool] = mapped_column(default=True)
    include_anomalies: Mapped[bool] = mapped_column(default=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (Index("ix_export_jobs_status", "status"),)
