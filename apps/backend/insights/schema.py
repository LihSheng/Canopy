import json
import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class GeneratedInsightModel(Base):
    __tablename__ = "generated_insights"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    current_month: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    recommendations_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    key_findings_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
    anomaly_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    department_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_payroll: Mapped[float] = mapped_column(Numeric(12, 2, asdecimal=False), nullable=False, default=0.0)
    total_claims: Mapped[float] = mapped_column(Numeric(12, 2, asdecimal=False), nullable=False, default=0.0)

    __table_args__ = (
        Index(
            "ix_generated_insights_snapshot_month",
            "snapshot_id",
            "current_month",
            unique=True,
        ),
    )

    @classmethod
    def pack_list(cls, items: list[str]) -> str:
        return json.dumps(items)

    @classmethod
    def unpack_list(cls, payload_json: str) -> list[str]:
        try:
            return json.loads(payload_json)
        except (json.JSONDecodeError, TypeError):
            return []
