import threading
import time
from unittest.mock import MagicMock

import pytest

from job_queue.job_registry import JobRegistry, JobStatus
from job_queue.tenant_queue import TenantJobQueue


class TestJobRegistry:
    def test_register_job_returns_uuid_and_tracks_status(self):
        registry = JobRegistry()
        job_id = registry.register_job("tenant-a", "provision")
        assert job_id is not None
        assert len(job_id) == 36

        job = registry.get_job(job_id)
        assert job["tenant_id"] == "tenant-a"
        assert job["job_type"] == "provision"
        assert job["status"] == JobStatus.PENDING.value

    def test_update_status_transitions(self):
        registry = JobRegistry()
        job_id = registry.register_job("tenant-a", "refresh")
        registry.update_status(job_id, JobStatus.RUNNING.value)
        job = registry.get_job(job_id)
        assert job["status"] == JobStatus.RUNNING.value
        assert job["started_at"] is not None

    def test_update_status_to_completed_sets_finished(self):
        registry = JobRegistry()
        job_id = registry.register_job("tenant-a", "refresh")
        registry.update_status(job_id, JobStatus.RUNNING.value)
        registry.update_status(job_id, JobStatus.COMPLETED.value)
        job = registry.get_job(job_id)
        assert job["status"] == JobStatus.COMPLETED.value
        assert job["finished_at"] is not None

    def test_update_status_failed_with_error(self):
        registry = JobRegistry()
        job_id = registry.register_job("tenant-a", "refresh")
        registry.update_status(job_id, JobStatus.FAILED.value, error="Timeout")
        job = registry.get_job(job_id)
        assert job["status"] == JobStatus.FAILED.value
        assert job["error_message"] == "Timeout"

    def test_get_tenant_active_jobs_counts_running_only(self):
        registry = JobRegistry()
        j1 = registry.register_job("tenant-a", "t1")
        j2 = registry.register_job("tenant-a", "t2")
        j3 = registry.register_job("tenant-a", "t3")
        registry.update_status(j1, JobStatus.RUNNING.value)
        registry.update_status(j2, JobStatus.RUNNING.value)
        registry.update_status(j3, JobStatus.PENDING.value)
        assert registry.get_tenant_active_jobs("tenant-a") == 2

    def test_get_tenant_active_jobs_zero_for_other_tenant(self):
        registry = JobRegistry()
        j1 = registry.register_job("tenant-a", "t1")
        registry.update_status(j1, JobStatus.RUNNING.value)
        assert registry.get_tenant_active_jobs("tenant-b") == 0

    def test_get_tenant_jobs_filters_by_status(self):
        registry = JobRegistry()
        j1 = registry.register_job("tenant-a", "t1")
        j2 = registry.register_job("tenant-a", "t2")
        registry.update_status(j1, JobStatus.COMPLETED.value)
        registry.update_status(j2, JobStatus.RUNNING.value)
        completed = registry.get_tenant_jobs("tenant-a", JobStatus.COMPLETED.value)
        assert len(completed) == 1
        assert completed[0]["job_id"] == j1

    def test_get_tenant_jobs_returns_all_when_no_status(self):
        registry = JobRegistry()
        registry.register_job("tenant-a", "t1")
        registry.register_job("tenant-a", "t2")
        all_jobs = registry.get_tenant_jobs("tenant-a")
        assert len(all_jobs) == 2


class TestTenantJobQueue:
    def test_enqueue_adds_job_to_tenant_queue(self):
        job_queue = TenantJobQueue(max_concurrent_global=10)
        results = []

        def task(x):
            results.append(x)

        job_queue.enqueue("tenant-a", task, 42)
        item = job_queue.dequeue()
        assert item is not None
        job_id, callable_fn, args, kwargs = item
        callable_fn(*args, **kwargs)
        assert results == [42]

    def test_enqueue_preserves_tenant_isolation(self):
        job_queue = TenantJobQueue(max_concurrent_global=10)
        results_a = []
        results_b = []

        def task_a(x):
            results_a.append(("a", x))

        def task_b(x):
            results_b.append(("b", x))

        job_queue.enqueue("tenant-a", task_a, 1)
        job_queue.enqueue("tenant-a", task_a, 2)
        job_queue.enqueue("tenant-b", task_b, 10)
        job_queue.enqueue("tenant-b", task_b, 20)

        items = []
        for _ in range(4):
            item = job_queue.dequeue()
            if item:
                items.append(item)

        assert len(items) == 4
        tenant_a_items = [i for i in items if i[2][0] == 1 or i[2][0] == 2]
        tenant_b_items = [i for i in items if i[2][0] == 10 or i[2][0] == 20]
        assert len(tenant_a_items) == 2
        assert len(tenant_b_items) == 2

    def test_round_robin_fairness(self):
        job_queue = TenantJobQueue(max_concurrent_global=10)
        for i in range(5):
            job_queue.enqueue("tenant-a", lambda: None)
        for i in range(5):
            job_queue.enqueue("tenant-b", lambda: None)

        items = []
        for _ in range(10):
            item = job_queue.dequeue()
            if item:
                items.append(item)

        tenant_a_count = 0
        tenant_b_count = 0
        for item in items:
            jid = item[0]
            job = job_queue.registry.get_job(jid)
            if job["tenant_id"] == "tenant-a":
                tenant_a_count += 1
            elif job["tenant_id"] == "tenant-b":
                tenant_b_count += 1
        assert tenant_a_count == 5
        assert tenant_b_count == 5

    def test_concurrency_cap_prevents_excess(self):
        job_queue = TenantJobQueue(max_concurrent_global=10)
        for _ in range(10):
            job_queue.enqueue("tenant-a", lambda: None)

        items = []
        for _ in range(10):
            item = job_queue.dequeue()
            if item:
                items.append(item)

        assert len(items) <= 5

    def test_dequeue_returns_none_when_empty(self):
        job_queue = TenantJobQueue()
        assert job_queue.dequeue() is None

    def test_dequeue_returns_none_when_global_limit_reached(self):
        job_queue = TenantJobQueue(max_concurrent_global=1)
        job_queue.enqueue("tenant-a", lambda: None)
        first = job_queue.dequeue()
        assert first is not None
        second = job_queue.dequeue()
        assert second is None

    def test_no_tenant_starvation(self):
        job_queue = TenantJobQueue(max_concurrent_global=10)
        job_queue.enqueue("tenant-a", lambda: None)
        job_queue.enqueue("tenant-b", lambda: None)

        items = []
        for _ in range(2):
            item = job_queue.dequeue()
            if item:
                items.append(item)

        tenant_ids = set()
        for item in items:
            job_id = item[0]
            job = job_queue.registry.get_job(job_id)
            tenant_ids.add(job["tenant_id"])

        assert len(tenant_ids) == 2

    def test_start_and_stop(self):
        job_queue = TenantJobQueue(max_concurrent_global=10)
        job_queue.start()
        assert job_queue._running is True
        job_queue.stop()
        assert job_queue._running is False

    def test_job_lifecycle_pending_to_completed(self):
        job_queue = TenantJobQueue(max_concurrent_global=10)
        completed = []

        def task():
            completed.append(True)

        job_id = job_queue.enqueue("tenant-a", task)
        job_before = job_queue.registry.get_job(job_id)
        assert job_before["status"] == JobStatus.PENDING.value

        item = job_queue.dequeue()
        assert item is not None
        jid, callable_fn, args, kwargs = item
        callable_fn(*args, **kwargs)
        job_queue.registry.update_status(jid, JobStatus.COMPLETED.value)

        job_after = job_queue.registry.get_job(job_id)
        assert len(completed) == 1
        assert job_after["status"] == JobStatus.COMPLETED.value

    def test_job_lifecycle_pending_to_failed(self):
        job_queue = TenantJobQueue(max_concurrent_global=10)

        def failing_task():
            raise ValueError("simulated failure")

        job_id = job_queue.enqueue("tenant-a", failing_task)
        item = job_queue.dequeue()
        assert item is not None
        jid, callable_fn, args, kwargs = item
        try:
            callable_fn(*args, **kwargs)
        except Exception:
            job_queue.registry.update_status(jid, JobStatus.FAILED.value, error="simulated failure")

        job_after = job_queue.registry.get_job(job_id)
        assert job_after["status"] == JobStatus.FAILED.value
        assert job_after["error_message"] == "simulated failure"

    def test_registry_and_tracker_exposed(self):
        job_queue = TenantJobQueue()
        assert isinstance(job_queue.registry, JobRegistry)
        assert job_queue.tracker is job_queue._tracker

    def test_queue_is_thread_safe(self):
        job_queue = TenantJobQueue(max_concurrent_global=200)
        errors = []

        def enqueue_many(tid, count):
            try:
                for _ in range(count):
                    job_queue.enqueue(tid, lambda: None)
            except Exception as e:
                errors.append(e)

        threads = []
        for i in range(4):
            t = threading.Thread(target=enqueue_many, args=(f"tenant-{i}", 50))
            threads.append(t)
            t.start()

        for t in threads:
            t.join()

        assert len(errors) == 0

        total_jobs = 0
        for tid in [f"tenant-{i}" for i in range(4)]:
            total_jobs += len(job_queue.registry.get_tenant_jobs(tid))
        assert total_jobs == 200

    def test_dequeue_skips_tenant_at_concurrency_cap(self):
        job_queue = TenantJobQueue(max_concurrent_global=20)
        for _ in range(6):
            job_queue.enqueue("tenant-a", lambda: None)
        job_queue.enqueue("tenant-b", lambda: None)

        remaining_a = len(job_queue._queues.get("tenant-a", []))
        remaining_b = len(job_queue._queues.get("tenant-b", []))

        total_pending = remaining_a + remaining_b
        assert total_pending == 7

        items = []
        for _ in range(20):
            item = job_queue.dequeue()
            if item:
                items.append(item)

        assert len(items) > 0

