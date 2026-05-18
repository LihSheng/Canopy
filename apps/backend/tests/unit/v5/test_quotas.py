import threading

import pytest

from v5.quotas.domain import LimitType, QuotaCheckResult, QuotaType, QuotaUsage
from v5.quotas.enforcer import QuotaEnforcer
from v5.quotas.errors import QuotaExceededError
from v5.quotas.evaluator import QuotaEvaluator
from v5.quotas.registry import DEFAULT_QUOTAS, get_quota_definition
from v5.quotas.usage_tracker import UsageTracker


class TestDefaultQuotas:
    def test_all_quota_types_have_definitions(self):
        for qt in QuotaType:
            assert qt in DEFAULT_QUOTAS

    def test_storage_bytes_is_hard_limit(self):
        quota = get_quota_definition(QuotaType.STORAGE_BYTES)
        assert quota.limit_type == LimitType.HARD
        assert quota.max_value == 10 * 1024 * 1024 * 1024
        assert quota.warning_threshold_pct == 0.80

    def test_concurrent_jobs_is_hard_limit(self):
        quota = get_quota_definition(QuotaType.CONCURRENT_JOBS)
        assert quota.limit_type == LimitType.HARD
        assert quota.max_value == 5

    def test_jobs_per_hour_is_soft_limit(self):
        quota = get_quota_definition(QuotaType.JOBS_PER_HOUR)
        assert quota.limit_type == LimitType.SOFT
        assert quota.max_value == 100

    def test_rows_per_batch_is_hard_limit(self):
        quota = get_quota_definition(QuotaType.ROWS_PER_BATCH)
        assert quota.limit_type == LimitType.HARD
        assert quota.max_value == 1_000_000

    def test_upload_size_is_hard_limit(self):
        quota = get_quota_definition(QuotaType.UPLOAD_SIZE_BYTES)
        assert quota.limit_type == LimitType.HARD
        assert quota.max_value == 100 * 1024 * 1024

    def test_api_requests_is_soft_limit(self):
        quota = get_quota_definition(QuotaType.API_REQUESTS_PER_MINUTE)
        assert quota.limit_type == LimitType.SOFT
        assert quota.max_value == 1000


class TestUsageTracker:
    def test_increment_returns_new_count(self):
        tracker = UsageTracker()
        count = tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, 1)
        assert count == 1
        count = tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, 2)
        assert count == 3

    def test_decrement_returns_new_count(self):
        tracker = UsageTracker()
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, 5)
        count = tracker.decrement("tenant-a", QuotaType.CONCURRENT_JOBS, 2)
        assert count == 3

    def test_decrement_does_not_go_below_zero(self):
        tracker = UsageTracker()
        count = tracker.decrement("tenant-a", QuotaType.CONCURRENT_JOBS, 1)
        assert count == 0

    def test_get_current_returns_zero_for_untracked(self):
        tracker = UsageTracker()
        assert tracker.get_current("tenant-none", QuotaType.CONCURRENT_JOBS) == 0

    def test_reset_single_quota_type(self):
        tracker = UsageTracker()
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, 3)
        tracker.increment("tenant-a", QuotaType.STORAGE_BYTES, 1000)
        tracker.reset("tenant-a", QuotaType.CONCURRENT_JOBS)
        assert tracker.get_current("tenant-a", QuotaType.CONCURRENT_JOBS) == 0
        assert tracker.get_current("tenant-a", QuotaType.STORAGE_BYTES) == 1000

    def test_reset_all_quota_types(self):
        tracker = UsageTracker()
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, 3)
        tracker.increment("tenant-a", QuotaType.STORAGE_BYTES, 1000)
        tracker.increment("tenant-b", QuotaType.CONCURRENT_JOBS, 5)
        tracker.reset("tenant-a")
        assert tracker.get_current("tenant-a", QuotaType.CONCURRENT_JOBS) == 0
        assert tracker.get_current("tenant-a", QuotaType.STORAGE_BYTES) == 0
        assert tracker.get_current("tenant-b", QuotaType.CONCURRENT_JOBS) == 5

    def test_concurrent_count_is_thread_safe(self):
        tracker = UsageTracker()
        errors = []

        def increment_many(tid: str, n: int):
            try:
                for _ in range(n):
                    tracker.increment(tid, QuotaType.CONCURRENT_JOBS, 1)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(10):
            t = threading.Thread(target=increment_many, args=(f"t-{i%3}", 100))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0
        total = sum(
            tracker.get_current(f"t-{i}", QuotaType.CONCURRENT_JOBS)
            for i in range(3)
        )
        assert total == 1000

    def test_rolling_window_prunes_old_entries(self):
        tracker = UsageTracker()
        tracker.increment("tenant-a", QuotaType.API_REQUESTS_PER_MINUTE, 1)
        assert tracker.get_current("tenant-a", QuotaType.API_REQUESTS_PER_MINUTE) == 1


class TestQuotaEvaluator:
    def test_check_quota_within_limit_allows(self):
        evaluator = QuotaEvaluator()
        tracker = UsageTracker()
        result = evaluator.check_quota(
            tracker, "tenant-a", QuotaType.CONCURRENT_JOBS, proposed_delta=1
        )
        assert result.allowed is True
        assert result.warning_triggered is False

    def test_check_quota_exceeds_hard_limit_denies(self):
        evaluator = QuotaEvaluator()
        tracker = UsageTracker()
        quota = get_quota_definition(QuotaType.CONCURRENT_JOBS)
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, quota.max_value)
        result = evaluator.check_quota(
            tracker, "tenant-a", QuotaType.CONCURRENT_JOBS, proposed_delta=1
        )
        assert result.allowed is False
        assert result.limit_type == LimitType.HARD
        assert result.warning_triggered is True

    def test_check_quota_exceeds_soft_limit_allows_with_warning(self):
        evaluator = QuotaEvaluator()
        tracker = UsageTracker()
        quota = get_quota_definition(QuotaType.JOBS_PER_HOUR)
        tracker.increment("tenant-a", QuotaType.JOBS_PER_HOUR, quota.max_value)
        result = evaluator.check_quota(
            tracker, "tenant-a", QuotaType.JOBS_PER_HOUR, proposed_delta=1
        )
        assert result.allowed is True
        assert result.limit_type == LimitType.SOFT
        assert result.warning_triggered is True

    def test_warning_triggered_at_threshold(self):
        evaluator = QuotaEvaluator()
        tracker = UsageTracker()
        quota = get_quota_definition(QuotaType.CONCURRENT_JOBS)
        threshold = int(quota.max_value * quota.warning_threshold_pct)
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, threshold)
        result = evaluator.check_quota(
            tracker, "tenant-a", QuotaType.CONCURRENT_JOBS
        )
        assert result.allowed is True
        assert result.warning_triggered is True

    def test_warning_not_triggered_below_threshold(self):
        evaluator = QuotaEvaluator()
        tracker = UsageTracker()
        quota = get_quota_definition(QuotaType.CONCURRENT_JOBS)
        threshold = int(quota.max_value * quota.warning_threshold_pct) - 1
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, max(threshold, 1))
        result = evaluator.check_quota(
            tracker, "tenant-a", QuotaType.CONCURRENT_JOBS
        )
        assert result.warning_triggered is False

    def test_get_tenant_quota_returns_custom_config(self):
        class MockConfigRepo:
            def get_config(self, tenant_id, key):
                if key == "concurrent_jobs":
                    import json
                    fake = type(
                        "FakeConfig",
                        (),
                        {"config_value_json": json.dumps({"max_value": 10, "limit_type": "hard"})},
                    )
                    return fake()
                return None

        evaluator = QuotaEvaluator(config_repository=MockConfigRepo())
        quota = evaluator.get_tenant_quota("tenant-a", QuotaType.CONCURRENT_JOBS)
        assert quota.max_value == 10

    def test_get_tenant_quota_falls_back_to_default_on_error(self):
        class FailingConfigRepo:
            def get_config(self, tenant_id, key):
                raise RuntimeError("DB down")

        evaluator = QuotaEvaluator(config_repository=FailingConfigRepo())
        quota = evaluator.get_tenant_quota("tenant-a", QuotaType.CONCURRENT_JOBS)
        assert quota.max_value == DEFAULT_QUOTAS[QuotaType.CONCURRENT_JOBS].max_value

    def test_get_usage_returns_correct_values(self):
        evaluator = QuotaEvaluator()
        tracker = UsageTracker()
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, 2)
        usage = evaluator.get_usage(tracker, "tenant-a", QuotaType.CONCURRENT_JOBS)
        assert isinstance(usage, QuotaUsage)
        assert usage.current_value == 2
        assert usage.max_value == 5
        assert usage.is_exceeded is False
        assert usage.available == 3

    def test_get_usage_shows_exceeded(self):
        evaluator = QuotaEvaluator()
        tracker = UsageTracker()
        quota = get_quota_definition(QuotaType.CONCURRENT_JOBS)
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, quota.max_value + 1)
        usage = evaluator.get_usage(tracker, "tenant-a", QuotaType.CONCURRENT_JOBS)
        assert usage.is_exceeded is True
        assert usage.available == 0

    def test_would_exceed_returns_true_for_hard_limit(self):
        evaluator = QuotaEvaluator()
        tracker = UsageTracker()
        quota = get_quota_definition(QuotaType.CONCURRENT_JOBS)
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, quota.max_value)
        assert evaluator.would_exceed(tracker, "tenant-a", QuotaType.CONCURRENT_JOBS, 1) is True

    def test_would_exceed_returns_false_within_limits(self):
        evaluator = QuotaEvaluator()
        tracker = UsageTracker()
        assert evaluator.would_exceed(tracker, "tenant-a", QuotaType.CONCURRENT_JOBS, 1) is False

    def test_get_all_quota_status_returns_all_types(self):
        evaluator = QuotaEvaluator()
        tracker = UsageTracker()
        results = evaluator.get_all_quota_status(tracker, "tenant-a")
        assert len(results) == len(QuotaType)
        for r in results:
            assert isinstance(r, QuotaCheckResult)


class TestQuotaEnforcer:
    def test_check_and_reserve_within_limit(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        enforcer = QuotaEnforcer(evaluator, tracker)
        result = enforcer.check_and_reserve("tenant-a", QuotaType.CONCURRENT_JOBS, 1)
        assert result.allowed is True
        assert tracker.get_current("tenant-a", QuotaType.CONCURRENT_JOBS) == 1

    def test_check_and_reserve_exceeds_hard_limit_denies(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        enforcer = QuotaEnforcer(evaluator, tracker)
        quota = get_quota_definition(QuotaType.CONCURRENT_JOBS)
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, quota.max_value)
        result = enforcer.check_and_reserve("tenant-a", QuotaType.CONCURRENT_JOBS, 1)
        assert result.allowed is False
        assert tracker.get_current("tenant-a", QuotaType.CONCURRENT_JOBS) == quota.max_value

    def test_release_decrements_correctly(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        enforcer = QuotaEnforcer(evaluator, tracker)
        enforcer.check_and_reserve("tenant-a", QuotaType.CONCURRENT_JOBS, 3)
        enforcer.release("tenant-a", QuotaType.CONCURRENT_JOBS, 2)
        assert tracker.get_current("tenant-a", QuotaType.CONCURRENT_JOBS) == 1

    def test_enforce_hard_limits_raises_on_exceed(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        enforcer = QuotaEnforcer(evaluator, tracker)
        quota = get_quota_definition(QuotaType.CONCURRENT_JOBS)
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, quota.max_value + 1)
        with pytest.raises(QuotaExceededError) as exc_info:
            enforcer.enforce_hard_limits("tenant-a", QuotaType.CONCURRENT_JOBS)
        assert exc_info.value.quota_type == "concurrent_jobs"

    def test_enforce_hard_limits_does_not_raise_on_soft_exceed(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        enforcer = QuotaEnforcer(evaluator, tracker)
        quota = get_quota_definition(QuotaType.JOBS_PER_HOUR)
        tracker.increment("tenant-a", QuotaType.JOBS_PER_HOUR, quota.max_value + 1)
        enforcer.enforce_hard_limits("tenant-a", QuotaType.JOBS_PER_HOUR)

    def test_enforce_with_warning_returns_result(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        enforcer = QuotaEnforcer(evaluator, tracker)
        result = enforcer.enforce_with_warning("tenant-a", QuotaType.CONCURRENT_JOBS)
        assert isinstance(result, QuotaCheckResult)
        assert result.allowed is True

    def test_enforce_with_warning_raises_on_hard_exceed(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        enforcer = QuotaEnforcer(evaluator, tracker)
        quota = get_quota_definition(QuotaType.CONCURRENT_JOBS)
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, quota.max_value + 1)
        with pytest.raises(QuotaExceededError):
            enforcer.enforce_with_warning("tenant-a", QuotaType.CONCURRENT_JOBS)
