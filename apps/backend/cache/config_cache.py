from cache.cache_store import CacheStore


class ConfigCache:
    def __init__(self, store: CacheStore, config_repository=None):
        self._store = store
        self._config_repository = config_repository
        self._prefix = "config:"

    def _key(self, tenant_id: str, key: str) -> str:
        return f"{self._prefix}{tenant_id}:{key}"

    def get_tenant_config(self, tenant_id: str, key: str) -> str | None:
        cache_key = self._key(tenant_id, key)
        cached = self._store.get(cache_key)
        if cached is not None:
            return cached

        if self._config_repository is None:
            return None

        config = self._config_repository.get_config(tenant_id, key)
        if config is None:
            return None

        value = config.config_value_json
        self.cache_tenant_config(tenant_id, key, value)
        return value

    def cache_tenant_config(
        self, tenant_id: str, key: str, value: str, ttl_seconds: int = 120
    ) -> None:
        self._store.set(self._key(tenant_id, key), value, ttl_seconds)

    def invalidate_tenant(self, tenant_id: str) -> None:
        prefix = f"{self._prefix}{tenant_id}:"
        self._store.delete_by_prefix(prefix)

    def invalidate_config(self, tenant_id: str, key: str) -> None:
        self._store.delete(self._key(tenant_id, key))

    def invalidate_all(self) -> None:
        self._store.delete_by_prefix(self._prefix)

