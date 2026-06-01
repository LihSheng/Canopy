from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class RetentionMode(StrEnum):
    RETAIN_INDEFINITELY = "retain_indefinitely"
    EXPIRE_AFTER = "expire_after"
    REVIEW_AFTER = "review_after"


class RetentionPreset(StrEnum):
    RETAIN_INDEFINITELY = "retain_indefinitely"
    DAYS_30 = "30_days"
    DAYS_90 = "90_days"
    YEAR_1 = "1_year"
    YEAR_7 = "7_years"
    CUSTOM = "custom"


PRESET_HORIZON_MAP: dict[str, int] = {
    RetentionPreset.DAYS_30.value: 30,
    RetentionPreset.DAYS_90.value: 90,
    RetentionPreset.YEAR_1.value: 365,
    RetentionPreset.YEAR_7.value: 2555,
}


@dataclass
class RetentionPolicy:
    id: str
    dataset_id: str
    tenant_id: str
    mode: str = RetentionMode.RETAIN_INDEFINITELY.value
    horizon_days: int | None = None
    preset: str = RetentionPreset.RETAIN_INDEFINITELY.value
    is_active: bool = True
    calculated_next_action_at: datetime | None = None
    created_by: str = ""
    updated_by: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


# Event type constants for audit records
AUDIT_EVENT_RETENTION_CREATED = "retention.policy.created"
AUDIT_EVENT_RETENTION_UPDATED = "retention.policy.updated"
AUDIT_EVENT_RETENTION_DISABLED = "retention.policy.disabled"
