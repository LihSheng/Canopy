import threading
import time
from unittest.mock import MagicMock

from cache.cache_store import CacheStore
from cache.config_cache import ConfigCache
from cache.invalidation import CacheInvalidator
from cache.routing_cache import RoutingCache
from job_queue.tenant_queue import TenantJobQueue
from quotas.domain import QuotaType
from quotas.enforcer import QuotaEnforcer
from quotas.evaluator import QuotaEvaluator
from quotas.registry import get_quota_definition
from quotas.usage_tracker import UsageTracker


class TestFullQuotaEnforcementFlow:
    def test_usage_tracker_plus_evaluator_plus_enforcer(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        enforcer = QuotaEnforcer(evaluator, tracker)

        max_jobs = get_quota_definition(QuotaType.CONCURRENT_JOBS).max_value
        for i in range(max_jobs):
            result = enforcer.check_and_reserve("tenant-a", QuotaType.CONCURRENT_JOBS, 1)
            assert result.allowed is True

        result = enforcer.check_and_reserve("tenant-a", QuotaType.CONCURRENT_JOBS, 1)
        assert result.allowed is False

        enforcer.release("tenant-a", QuotaType.CONCURRENT_JOBS, 1)
        result = enforcer.check_and_reserve("tenant-a", QuotaType.CONCURRENT_JOBS, 1)
        assert result.allowed is True

    def test_soft_limit_warns_but_allows_progression(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        enforcer = QuotaEnforcer(evaluator, tracker)

        max_jobs_per_hour = get_quota_definition(QuotaType.JOBS_PER_HOUR).max_value
        for i in range(max_jobs_per_hour + 5):
            result = enforcer.enforce_with_warning("tenant-a", QuotaType.JOBS_PER_HOUR)
            assert result.allowed is True

    def test_hard_limit_stops_at_exact_limit(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        QuotaEnforcer(evaluator, tracker)

        max_rows = get_quota_definition(QuotaType.ROWS_PER_BATCH).max_value
        tracker.increment("tenant-a", QuotaType.ROWS_PER_BATCH, max_rows)
        result = evaluator.check_quota(tracker, "tenant-a", QuotaType.ROWS_PER_BATCH, proposed_delta=1)
        assert result.allowed is False

    def test_warning_threshold_triggers_before_hard_limit(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        quota = get_quota_definition(QuotaType.UPLOAD_SIZE_BYTES)
        threshold = int(quota.max_value * quota.warning_threshold_pct)

        tracker.increment("tenant-a", QuotaType.UPLOAD_SIZE_BYTES, threshold)
        result = evaluator.check_quota(tracker, "tenant-a", QuotaType.UPLOAD_SIZE_BYTES, proposed_delta=1)
        assert result.warning_triggered is True
        assert result.allowed is True

        remaining = quota.max_value - threshold
        tracker.increment("tenant-a", QuotaType.UPLOAD_SIZE_BYTES, remaining + 1)
        result = evaluator.check_quota(tracker, "tenant-a", QuotaType.UPLOAD_SIZE_BYTES, proposed_delta=1)
        assert result.allowed is False

    def test_multiple_tenants_independent_quotas(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        enforcer = QuotaEnforcer(evaluator, tracker)

        max_jobs = get_quota_definition(QuotaType.CONCURRENT_JOBS).max_value
        for _ in range(max_jobs):
            enforcer.check_and_reserve("tenant-a", QuotaType.CONCURRENT_JOBS, 1)

        result_a = enforcer.check_and_reserve("tenant-a", QuotaType.CONCURRENT_JOBS, 1)
        assert result_a.allowed is False

        result_b = enforcer.check_and_reserve("tenant-b", QuotaType.CONCURRENT_JOBS, 1)
        assert result_b.allowed is True


class TestQueueFairnessIntegration:
    def test_two_tenants_five_jobs_each_round_robin(self):
        job_queue = TenantJobQueue(max_concurrent_global=10)

        results = []

        def make_task(tenant_id, seq):
            def task():
                results.append((tenant_id, seq))

            return task

        for i in range(5):
            job_queue.enqueue("tenant-a", make_task("tenant-a", i))
        for i in range(5):
            job_queue.enqueue("tenant-b", make_task("tenant-b", i))

        items = []
        for _ in range(10):
            item = job_queue.dequeue()
            if item:
                items.append(item)

        assert len(items) == 10

        for _, callable_fn, _, _ in items:
            callable_fn()

        assert len(results) == 10
        a_results = [r for r in results if r[0] == "tenant-a"]
        b_results = [r for r in results if r[0] == "tenant-b"]
        assert len(a_results) == 5
        assert len(b_results) == 5

    def test_concurrency_cap_per_tenant_prevent_excess(self):
        job_queue = TenantJobQueue(max_concurrent_global=30)
        for _ in range(10):
            job_queue.enqueue("tenant-a", lambda: None)

        items = []
        for _ in range(15):
            item = job_queue.dequeue()
            if item:
                items.append(item)

        max_concurrent = get_quota_definition(QuotaType.CONCURRENT_JOBS).max_value
        assert len(items) <= max_concurrent

    def test_tenant_at_concurrency_cap_skipped(self):
        job_queue = TenantJobQueue(max_concurrent_global=30)
        tracker = job_queue.tracker
        max_jobs = get_quota_definition(QuotaType.CONCURRENT_JOBS).max_value
        tracker.increment("tenant-a", QuotaType.CONCURRENT_JOBS, max_jobs)

        job_queue.enqueue("tenant-a", lambda: None)
        job_queue.enqueue("tenant-b", lambda: None)

        item = job_queue.dequeue()
        if item:
            job_id = item[0]
            job = job_queue.registry.get_job(job_id)
            assert job["tenant_id"] == "tenant-b"

    def test_all_tenants_get_serviced_no_starvation(self):
        job_queue = TenantJobQueue(max_concurrent_global=30)
        tenant_ids = ["aa", "bb", "cc", "dd", "ee"]
        for tid in tenant_ids:
            for _ in range(3):
                job_queue.enqueue(tid, lambda: None)

        items = []
        for _ in range(15):
            item = job_queue.dequeue()
            if item:
                items.append(item)

        assert len(items) == 15

        tenant_seen = set()
        for item in items:
            job_id = item[0]
            job = job_queue.registry.get_job(job_id)
            tenant_seen.add(job["tenant_id"])

        assert len(tenant_seen) == 5

    def test_queue_with_real_threads(self):
        job_queue = TenantJobQueue(max_concurrent_global=10)
        results: list[str] = []

        def make_task(label):
            def task():
                time.sleep(0.02)
                results.append(label)

            return task

        for i in range(3):
            job_queue.enqueue("tenant-a", make_task(f"a-{i}"))
        for i in range(3):
            job_queue.enqueue("tenant-b", make_task(f"b-{i}"))

        items = []
        for _ in range(6):
            item = job_queue.dequeue()
            if item:
                items.append(item)

        threads = []
        for jid, callable_fn, args, kwargs in items:
            t = threading.Thread(target=callable_fn, args=args, kwargs=kwargs, daemon=True)
            threads.append(t)
            t.start()

        for t in threads:
            t.join(timeout=5)

        assert len(results) == 6


class TestCacheInvalidationIntegration:
    def test_suspend_tenant_triggers_cache_miss(self):
        store = CacheStore()
        call_count = 0

        class MockSession:
            def close(self):
                pass

            def query(self, model):
                nonlocal call_count
                call_count += 1

                class MockQuery:
                    def filter(self, *args):
                        return self

                    def first(self):
                        return type(
                            "FakeTarget",
                            (),
                            {
                                "database_kind": "tenant_data",
                                "connection_ref": "pg://suspended",
                                "tenant_id": "tenant-x",
                            },
                        )()

                return MockQuery()

        db_factory = MagicMock(return_value=MockSession())
        routing = RoutingCache(store, db_factory)
        config_cache = ConfigCache(store)
        invalidator = CacheInvalidator(routing, config_cache)

        routing.get_tenant_database_target("tenant-x")
        assert call_count == 1

        invalidator.on_tenant_suspended("tenant-x")

        routing.get_tenant_database_target("tenant-x")
        assert call_count == 2

    def test_config_change_invalidates_cache(self):
        store = CacheStore()

        class FakeConfig:
            def __init__(self, value):
                self.config_value_json = value

        class MockRepo:
            def __init__(self):
                self.values: dict[str, str] = {"feature_flag": '{"enabled":true}'}

            def get_config(self, tenant_id, key):
                return FakeConfig(self.values.get(key, ""))

        repo = MockRepo()
        config_cache = ConfigCache(store, config_repository=repo)

        v1 = config_cache.get_tenant_config("tenant-x", "feature_flag")
        assert v1 == '{"enabled":true}'

        config_cache.invalidate_config("tenant-x", "feature_flag")

        repo.values["feature_flag"] = '{"enabled":false}'
        v2 = config_cache.get_tenant_config("tenant-x", "feature_flag")
        assert v2 == '{"enabled":false}'

    def test_database_rotation_invalidates_routing(self):
        store = CacheStore()
        call_count = 0

        class MockSession:
            def close(self):
                pass

            def query(self, model):
                nonlocal call_count
                call_count += 1
                ref = "pg://rotated" if call_count > 1 else "pg://original"

                class MockQuery:
                    def filter(self, *args):
                        return self

                    def first(self):
                        return type(
                            "FakeTarget",
                            (),
                            {
                                "database_kind": "tenant_data",
                                "connection_ref": ref,
                                "tenant_id": "tenant-x",
                            },
                        )()

                return MockQuery()

        db_factory = MagicMock(return_value=MockSession())
        routing = RoutingCache(store, db_factory)
        config_cache = ConfigCache(store)
        invalidator = CacheInvalidator(routing, config_cache)

        result1 = routing.get_tenant_database_target("tenant-x")
        assert result1["connection_ref"] == "pg://original"

        invalidator.on_database_rotation("tenant-x", "pg://original", "pg://rotated")

        result2 = routing.get_tenant_database_target("tenant-x")
        assert result2["connection_ref"] == "pg://rotated"

    def test_provisioning_triggers_cache_invalidation(self):
        store = CacheStore()

        class MockSession:
            def close(self):
                pass

            def query(self, model):
                class MockQuery:
                    def filter(self, *args):
                        return self

                    def first(self):
                        return type(
                            "FakeTarget",
                            (),
                            {
                                "database_kind": "tenant_data",
                                "connection_ref": "pg://new",
                                "tenant_id": "new-tenant",
                            },
                        )()

                return MockQuery()

        db_factory = MagicMock(return_value=MockSession())
        routing = RoutingCache(store, db_factory)
        config_cache = ConfigCache(store)
        invalidator = CacheInvalidator(routing, config_cache)

        routing.cache_tenant_database_target("new-tenant", {"stale": True})
        assert store.get("routing:new-tenant") is not None

        invalidator.on_tenant_provisioned("new-tenant")
        assert store.get("routing:new-tenant") is None

    def test_schema_rollout_invalidates_all_routing(self):
        store = CacheStore()
        routing = RoutingCache(store, MagicMock())
        config_cache = ConfigCache(store)
        invalidator = CacheInvalidator(routing, config_cache)

        routing.cache_tenant_database_target("t1", {"x": 1})
        routing.cache_tenant_database_target("t2", {"x": 2})
        routing.cache_tenant_database_target("t3", {"x": 3})

        assert store.get("routing:t1") is not None

        invalidator.on_schema_rollout()

        assert store.get("routing:t1") is None
        assert store.get("routing:t2") is None
        assert store.get("routing:t3") is None


class TestEndToEndQuotaQueueCache:
    def test_quota_enforcer_prevents_queue_overrun(self):
        tracker = UsageTracker()
        evaluator = QuotaEvaluator()
        enforcer = QuotaEnforcer(evaluator, tracker)
        job_queue = TenantJobQueue(max_concurrent_global=10)

        job_queue.enqueue("tenant-a", lambda: None)
        max_jobs = get_quota_definition(QuotaType.CONCURRENT_JOBS).max_value
        for _ in range(max_jobs):
            enforcer.check_and_reserve("tenant-a", QuotaType.CONCURRENT_JOBS, 1)

        result = enforcer.check_and_reserve("tenant-a", QuotaType.CONCURRENT_JOBS, 1)
        assert result.allowed is False

    def test_cache_and_queue_operate_independently(self):
        store = CacheStore()
        routing = RoutingCache(store, MagicMock())
        config_cache = ConfigCache(store)
        job_queue = TenantJobQueue()

        routing.cache_tenant_database_target("tenant-a", {"db": "pg://a"})
        config_cache.cache_tenant_config("tenant-a", "flag", "true")
        job_queue.enqueue("tenant-a", lambda: None)

        assert routing.get_tenant_database_target("tenant-a") is not None
        assert config_cache.get_tenant_config("tenant-a", "flag") == "true"
        assert len(job_queue.registry.get_tenant_jobs("tenant-a")) == 1
