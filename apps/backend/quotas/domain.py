from dataclasses import dataclass
from enum import Enum


class QuotaType(Enum):
    STORAGE_BYTES = "storage_bytes"
    CONCURRENT_JOBS = "concurrent_jobs"
    JOBS_PER_HOUR = "jobs_per_hour"
    ROWS_PER_BATCH = "rows_per_batch"
    UPLOAD_SIZE_BYTES = "upload_size_bytes"
    API_REQUESTS_PER_MINUTE = "api_requests_per_minute"


class LimitType(Enum):
    HARD = "hard"
    SOFT = "soft"


@dataclass
class QuotaDefinition:
    quota_type: QuotaType
    limit_type: LimitType
    max_value: int
    warning_threshold_pct: float = 0.80
    description: str = ""


@dataclass
class QuotaUsage:
    quota_type: QuotaType
    current_value: int
    max_value: int
    limit_type: LimitType
    is_exceeded: bool
    warning_triggered: bool
    available: int


@dataclass
class QuotaCheckResult:
    allowed: bool
    quota_type: QuotaType
    limit_type: LimitType
    current_value: int
    max_value: int
    warning_triggered: bool
    message: str
