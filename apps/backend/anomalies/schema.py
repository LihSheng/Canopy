import json
import uuid

from sqlalchemy import Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class DetectedAnomalyModel(Base):
    __tablename__ = "detected_anomalies"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    anomaly_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    target_entity_id: Mapped[str] = mapped_column(
        String(36), nullable=False, index=True
    )
    month_key: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    baseline_value: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    observed_value: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    delta_value: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    delta_percent: Mapped[float] = mapped_column(
        Float, nullable=False, default=0.0
    )
    severity: Mapped[str] = mapped_column(String(16), nullable=False, default="low")
    driver_payload_json: Mapped[str] = mapped_column(
        Text, nullable=False, default="[]"
    )

    @classmethod
    def pack_drivers(cls, driver_details: list[str]) -> str:
        return json.dumps(driver_details)

    @classmethod
    def unpack_drivers(cls, payload_json: str) -> list[str]:
        try:
            return json.loads(payload_json)
        except (json.JSONDecodeError, TypeError):
            return []
