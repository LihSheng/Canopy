import threading
import time
from typing import Any


class CacheStore:
    def __init__(self, default_ttl_seconds: int = 60):
        self._default_ttl = default_ttl_seconds
        self._lock = threading.Lock()
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any:
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, value = entry
            if time.monotonic() > expires_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        ttl = ttl_seconds if ttl_seconds is not None else self._default_ttl
        expires_at = time.monotonic() + ttl
        with self._lock:
            self._store[key] = (expires_at, value)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def delete_by_prefix(self, prefix: str) -> int:
        count = 0
        with self._lock:
            keys_to_delete = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._store[k]
                count += 1
        return count

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    def _cleanup_expired(self) -> int:
        now = time.monotonic()
        count = 0
        with self._lock:
            expired_keys = [k for k, (expires_at, _) in self._store.items() if now > expires_at]
            for k in expired_keys:
                del self._store[k]
                count += 1
        return count
