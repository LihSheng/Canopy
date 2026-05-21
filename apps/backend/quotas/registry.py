from quotas.domain import LimitType, QuotaDefinition, QuotaType

STORAGE_BYTES = 10 * 1024 * 1024 * 1024
CONCURRENT_JOBS = 5
JOBS_PER_HOUR = 100
ROWS_PER_BATCH = 1_000_000
UPLOAD_SIZE_BYTES = 100 * 1024 * 1024
API_REQUESTS_PER_MINUTE = 1000

DEFAULT_QUOTAS: dict[QuotaType, QuotaDefinition] = {
    QuotaType.STORAGE_BYTES: QuotaDefinition(
        quota_type=QuotaType.STORAGE_BYTES,
        limit_type=LimitType.HARD,
        max_value=STORAGE_BYTES,
        warning_threshold_pct=0.80,
        description="Maximum storage bytes per tenant",
    ),
    QuotaType.CONCURRENT_JOBS: QuotaDefinition(
        quota_type=QuotaType.CONCURRENT_JOBS,
        limit_type=LimitType.HARD,
        max_value=CONCURRENT_JOBS,
        warning_threshold_pct=0.80,
        description="Maximum concurrent jobs per tenant",
    ),
    QuotaType.JOBS_PER_HOUR: QuotaDefinition(
        quota_type=QuotaType.JOBS_PER_HOUR,
        limit_type=LimitType.SOFT,
        max_value=JOBS_PER_HOUR,
        warning_threshold_pct=0.80,
        description="Maximum jobs per hour per tenant",
    ),
    QuotaType.ROWS_PER_BATCH: QuotaDefinition(
        quota_type=QuotaType.ROWS_PER_BATCH,
        limit_type=LimitType.HARD,
        max_value=ROWS_PER_BATCH,
        warning_threshold_pct=0.80,
        description="Maximum rows per batch operation",
    ),
    QuotaType.UPLOAD_SIZE_BYTES: QuotaDefinition(
        quota_type=QuotaType.UPLOAD_SIZE_BYTES,
        limit_type=LimitType.HARD,
        max_value=UPLOAD_SIZE_BYTES,
        warning_threshold_pct=0.80,
        description="Maximum single upload size in bytes",
    ),
    QuotaType.API_REQUESTS_PER_MINUTE: QuotaDefinition(
        quota_type=QuotaType.API_REQUESTS_PER_MINUTE,
        limit_type=LimitType.SOFT,
        max_value=API_REQUESTS_PER_MINUTE,
        warning_threshold_pct=0.80,
        description="Maximum API requests per minute per tenant",
    ),
}


def get_quota_definition(quota_type: QuotaType) -> QuotaDefinition:
    return DEFAULT_QUOTAS[quota_type]
