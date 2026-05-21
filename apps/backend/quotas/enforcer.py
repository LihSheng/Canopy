from quotas.domain import LimitType, QuotaCheckResult, QuotaType
from quotas.errors import QuotaExceededError
from quotas.evaluator import QuotaEvaluator
from quotas.usage_tracker import UsageTracker


class QuotaEnforcer:
    def __init__(self, evaluator: QuotaEvaluator, tracker: UsageTracker):
        self._evaluator = evaluator
        self._tracker = tracker

    def check_and_reserve(self, tenant_id: str, quota_type: QuotaType, amount: int = 1) -> QuotaCheckResult:
        result = self._evaluator.check_quota(self._tracker, tenant_id, quota_type, proposed_delta=amount)
        if result.allowed:
            self._tracker.increment(tenant_id, quota_type, amount)
        return result

    def release(self, tenant_id: str, quota_type: QuotaType, amount: int = 1) -> None:
        self._tracker.decrement(tenant_id, quota_type, amount)

    def enforce_hard_limits(self, tenant_id: str, quota_type: QuotaType) -> None:
        result = self._evaluator.check_quota(self._tracker, tenant_id, quota_type)
        definition = self._evaluator.get_tenant_quota(tenant_id, quota_type)
        if definition.limit_type == LimitType.HARD and not result.allowed:
            raise QuotaExceededError(
                quota_type=quota_type.value,
                current=result.current_value,
                max_value=result.max_value,
                message=result.message,
            )

    def enforce_with_warning(self, tenant_id: str, quota_type: QuotaType) -> QuotaCheckResult:
        result = self._evaluator.check_quota(self._tracker, tenant_id, quota_type)
        definition = self._evaluator.get_tenant_quota(tenant_id, quota_type)
        if definition.limit_type == LimitType.HARD and not result.allowed:
            raise QuotaExceededError(
                quota_type=quota_type.value,
                current=result.current_value,
                max_value=result.max_value,
                message=result.message,
            )
        return result
