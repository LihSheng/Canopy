import threading
import time
from collections import defaultdict, deque

from common.executor import background
from quotas.domain import QuotaType
from quotas.registry import DEFAULT_QUOTAS
from quotas.usage_tracker import UsageTracker
from job_queue.job_registry import JobRegistry, JobStatus


class TenantJobQueue:
    def __init__(self, max_concurrent_global: int = 20):
        self._max_concurrent_global = max_concurrent_global
        self._lock = threading.Lock()
        self._queues: dict[str, deque] = defaultdict(deque)
        self._tenant_order: list[str] = []
        self._next_tenant_index: int = 0
        self._active_jobs: dict[str, int] = {}
        self._total_active: int = 0
        self._registry = JobRegistry()
        self._tracker = UsageTracker()
        self._running = False

    @property
    def registry(self) -> JobRegistry:
        return self._registry

    @property
    def tracker(self) -> UsageTracker:
        return self._tracker

    def enqueue(
        self, tenant_id: str, job_callable, *args, **kwargs
    ) -> str:
        job_id = self._registry.register_job(tenant_id, "generic")
        with self._lock:
            if tenant_id not in self._tenant_order:
                self._tenant_order.append(tenant_id)
            self._queues[tenant_id].append((job_id, job_callable, args, kwargs))
        return job_id

    def dequeue(self) -> tuple[str, callable, tuple, dict] | None:
        with self._lock:
            if self._total_active >= self._max_concurrent_global:
                return None
            if not self._tenant_order:
                return None

            start_index = self._next_tenant_index
            for _ in range(len(self._tenant_order)):
                idx = self._next_tenant_index % len(self._tenant_order)
                self._next_tenant_index = (idx + 1) % len(self._tenant_order)
                tenant_id = self._tenant_order[idx]

                if not self._queues.get(tenant_id):
                    continue

                active_for_tenant = self._active_jobs.get(tenant_id, 0)
                external_active = self._tracker.get_current(
                    tenant_id, QuotaType.CONCURRENT_JOBS
                )
                total_active = max(active_for_tenant, external_active)
                if total_active >= self._get_concurrency_cap(tenant_id):
                    continue

                job_id, job_callable, args, kwargs = self._queues[tenant_id].popleft()
                self._active_jobs[tenant_id] = active_for_tenant + 1
                self._total_active += 1
                self._tracker.increment(tenant_id, QuotaType.CONCURRENT_JOBS, 1)
                return (job_id, job_callable, args, kwargs)

            return None

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        background.run(
            target=self._dispatch_loop,
            name="tenant-queue-dispatcher",
        )

    def stop(self) -> None:
        self._running = False

    def _dispatch_loop(self) -> None:
        while self._running:
            item = self.dequeue()
            if item is None:
                time.sleep(0.05)
                continue

            job_id, job_callable, args, kwargs = item
            self._registry.update_status(job_id, JobStatus.RUNNING.value)

            background.run(
                target=self._execute_job,
                args=(job_id, job_callable, args, kwargs),
                name=f"tenant-job-{job_id}",
            )

    def _execute_job(
        self, job_id: str, job_callable, args: tuple, kwargs: dict
    ) -> None:
        tenant_id = None
        try:
            job = self._registry.get_job(job_id)
            if job:
                tenant_id = job["tenant_id"]
            job_callable(*args, **kwargs)
            self._registry.update_status(job_id, JobStatus.COMPLETED.value)
        except Exception as e:
            self._registry.update_status(
                job_id, JobStatus.FAILED.value, error=str(e)
            )
        finally:
            if tenant_id:
                with self._lock:
                    self._active_jobs[tenant_id] = max(
                        0, self._active_jobs.get(tenant_id, 1) - 1
                    )
                    self._total_active = max(0, self._total_active - 1)
                self._tracker.decrement(tenant_id, QuotaType.CONCURRENT_JOBS, 1)

    def _get_concurrency_cap(self, tenant_id: str) -> int:
        default = DEFAULT_QUOTAS.get(QuotaType.CONCURRENT_JOBS)
        return default.max_value if default else 5

