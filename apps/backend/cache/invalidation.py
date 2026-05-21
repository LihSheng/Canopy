from cache.config_cache import ConfigCache
from cache.routing_cache import RoutingCache


class CacheInvalidator:
    def __init__(self, routing_cache: RoutingCache, config_cache: ConfigCache):
        self._routing_cache = routing_cache
        self._config_cache = config_cache

    def on_tenant_provisioned(self, tenant_id: str) -> None:
        self._routing_cache.invalidate_tenant(tenant_id)

    def on_tenant_suspended(self, tenant_id: str) -> None:
        self._routing_cache.invalidate_tenant(tenant_id)

    def on_tenant_restored(self, tenant_id: str) -> None:
        self._routing_cache.invalidate_tenant(tenant_id)

    def on_tenant_config_changed(self, tenant_id: str, key: str | None = None) -> None:
        if key is not None:
            self._config_cache.invalidate_config(tenant_id, key)
        else:
            self._config_cache.invalidate_tenant(tenant_id)

    def on_database_rotation(self, tenant_id: str, old_ref: str, new_ref: str) -> None:
        self._routing_cache.invalidate_tenant(tenant_id)

    def on_schema_rollout(self) -> None:
        self._routing_cache.invalidate_all()
