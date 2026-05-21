from cache.cache_store import CacheStore


class RoutingCache:
    def __init__(self, store: CacheStore, db_session_factory):
        self._store = store
        self._db_session_factory = db_session_factory
        self._prefix = "routing:"

    def _key(self, tenant_id: str) -> str:
        return f"{self._prefix}{tenant_id}"

    def get_tenant_database_target(self, tenant_id: str) -> dict | None:
        cached = self._store.get(self._key(tenant_id))
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        session = self._db_session_factory()
        try:
            from control_plane.schemas.database_targets import (
                TenantDatabaseTargetModel,
            )

            target = (
                session.query(TenantDatabaseTargetModel)
                .filter(
                    TenantDatabaseTargetModel.tenant_id == tenant_id,
                    TenantDatabaseTargetModel.status == "active",
                )
                .first()
            )
            if target is None:
                return None

            result = {
                "database_kind": target.database_kind,
                "connection_ref": target.connection_ref,
                "tenant_id": target.tenant_id,
            }
            self.cache_tenant_database_target(tenant_id, result)
            return result
        finally:
            session.close()

    def cache_tenant_database_target(self, tenant_id: str, target: dict, ttl_seconds: int = 60) -> None:
        self._store.set(self._key(tenant_id), target, ttl_seconds)

    def invalidate_tenant(self, tenant_id: str) -> None:
        self._store.delete(self._key(tenant_id))

    def invalidate_all(self) -> None:
        self._store.delete_by_prefix(self._prefix)
