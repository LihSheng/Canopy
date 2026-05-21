import threading
import time

from quotas.domain import QuotaType


class UsageTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._counters: dict[str, dict[str, int]] = {}
        self._rolling_windows: dict[str, dict[str, list[float]]] = {}

    def _key(self, tenant_id: str, quota_type: QuotaType) -> str:
        return f"{tenant_id}:{quota_type.value}"

    def _init_tenant(self, tenant_id: str, quota_type: QuotaType) -> None:
        k = self._key(tenant_id, quota_type)
        if k not in self._counters:
            self._counters[k] = 0
        if k not in self._rolling_windows:
            self._rolling_windows[k] = []

    def increment(self, tenant_id: str, quota_type: QuotaType, amount: int = 1) -> int:
        with self._lock:
            self._init_tenant(tenant_id, quota_type)
            k = self._key(tenant_id, quota_type)
            self._counters[k] += amount
            if quota_type in (QuotaType.JOBS_PER_HOUR, QuotaType.API_REQUESTS_PER_MINUTE):
                now = time.monotonic()
                window = self._rolling_windows[k]
                self._prune_window(window, now, quota_type)
                for _ in range(amount):
                    window.append(now)
            return self._counters[k]

    def decrement(self, tenant_id: str, quota_type: QuotaType, amount: int = 1) -> int:
        with self._lock:
            self._init_tenant(tenant_id, quota_type)
            k = self._key(tenant_id, quota_type)
            self._counters[k] = max(0, self._counters[k] - amount)
            return self._counters[k]

    def get_current(self, tenant_id: str, quota_type: QuotaType) -> int:
        with self._lock:
            k = self._key(tenant_id, quota_type)
            if quota_type in (QuotaType.JOBS_PER_HOUR, QuotaType.API_REQUESTS_PER_MINUTE):
                now = time.monotonic()
                window = self._rolling_windows.get(k, [])
                self._prune_window(window, now, quota_type)
                return len(window)
            return self._counters.get(k, 0)

    def reset(self, tenant_id: str, quota_type: QuotaType | None = None) -> None:
        with self._lock:
            if quota_type is not None:
                k = self._key(tenant_id, quota_type)
                self._counters.pop(k, None)
                self._rolling_windows.pop(k, None)
            else:
                for t in list(self._counters.keys()):
                    if t.startswith(f"{tenant_id}:"):
                        self._counters.pop(t, None)
                for t in list(self._rolling_windows.keys()):
                    if t.startswith(f"{tenant_id}:"):
                        self._rolling_windows.pop(t, None)

    def _prune_window(
        self,
        window: list[float],
        now: float,
        quota_type: QuotaType,
    ) -> None:
        if quota_type == QuotaType.JOBS_PER_HOUR:
            cutoff = now - 3600
        elif quota_type == QuotaType.API_REQUESTS_PER_MINUTE:
            cutoff = now - 60
        else:
            return
        while window and window[0] < cutoff:
            window.pop(0)
