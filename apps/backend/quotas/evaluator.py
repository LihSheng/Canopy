import json

from quotas.domain import (
    LimitType,
    QuotaCheckResult,
    QuotaDefinition,
    QuotaType,
    QuotaUsage,
)
from quotas.registry import get_quota_definition
from quotas.usage_tracker import UsageTracker


class QuotaEvaluator:
    def __init__(self, config_repository=None):
        self._config_repository = config_repository

    def get_tenant_quota(self, tenant_id: str, quota_type: QuotaType) -> QuotaDefinition:
        default = get_quota_definition(quota_type)
        if self._config_repository is None:
            return default
        try:
            config = self._config_repository.get_config(tenant_id, quota_type.value)
            if config is None:
                return default
            data = json.loads(config.config_value_json)
            return QuotaDefinition(
                quota_type=quota_type,
                limit_type=LimitType(data.get("limit_type", default.limit_type.value)),
                max_value=data.get("max_value", default.max_value),
                warning_threshold_pct=data.get("warning_threshold_pct", default.warning_threshold_pct),
                description=data.get("description", default.description),
            )
        except Exception:
            return default

    def check_quota(
        self,
        tracker: UsageTracker,
        tenant_id: str,
        quota_type: QuotaType,
        proposed_delta: int = 0,
    ) -> QuotaCheckResult:
        definition = self.get_tenant_quota(tenant_id, quota_type)
        current_value = tracker.get_current(tenant_id, quota_type)
        projected = current_value + proposed_delta
        warning_threshold = int(definition.max_value * definition.warning_threshold_pct)
        warning_triggered = current_value >= warning_threshold

        if projected > definition.max_value:
            if definition.limit_type == LimitType.HARD:
                return QuotaCheckResult(
                    allowed=False,
                    quota_type=quota_type,
                    limit_type=definition.limit_type,
                    current_value=current_value,
                    max_value=definition.max_value,
                    warning_triggered=True,
                    message=(
                        f"Hard limit exceeded for {quota_type.value}: "
                        f"{projected} > {definition.max_value}. "
                        f"Current: {current_value}, proposed: {proposed_delta}"
                    ),
                )
            else:
                return QuotaCheckResult(
                    allowed=True,
                    quota_type=quota_type,
                    limit_type=definition.limit_type,
                    current_value=current_value,
                    max_value=definition.max_value,
                    warning_triggered=True,
                    message=(
                        f"Soft limit exceeded for {quota_type.value}: "
                        f"{projected} > {definition.max_value}. "
                        f"Operation allowed but monitor closely."
                    ),
                )

        return QuotaCheckResult(
            allowed=True,
            quota_type=quota_type,
            limit_type=definition.limit_type,
            current_value=current_value,
            max_value=definition.max_value,
            warning_triggered=warning_triggered,
            message=(
                f"Warning triggered for {quota_type.value}: {current_value}/{definition.max_value}"
                if warning_triggered
                else f"{quota_type.value}: {current_value}/{definition.max_value}"
            ),
        )

    def get_usage(
        self,
        tracker: UsageTracker,
        tenant_id: str,
        quota_type: QuotaType,
    ) -> QuotaUsage:
        definition = self.get_tenant_quota(tenant_id, quota_type)
        current_value = tracker.get_current(tenant_id, quota_type)
        warning_threshold = int(definition.max_value * definition.warning_threshold_pct)
        is_exceeded = current_value > definition.max_value
        warning_triggered = current_value >= warning_threshold
        available = max(0, definition.max_value - current_value)
        return QuotaUsage(
            quota_type=quota_type,
            current_value=current_value,
            max_value=definition.max_value,
            limit_type=definition.limit_type,
            is_exceeded=is_exceeded,
            warning_triggered=warning_triggered,
            available=available,
        )

    def get_all_quota_status(self, tracker: UsageTracker, tenant_id: str) -> list[QuotaCheckResult]:
        results: list[QuotaCheckResult] = []
        for quota_type in QuotaType:
            result = self.check_quota(tracker, tenant_id, quota_type)
            results.append(result)
        return results

    def would_exceed(
        self,
        tracker: UsageTracker,
        tenant_id: str,
        quota_type: QuotaType,
        proposed_delta: int,
    ) -> bool:
        result = self.check_quota(tracker, tenant_id, quota_type, proposed_delta)
        return not result.allowed
