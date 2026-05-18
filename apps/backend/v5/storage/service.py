from v5.storage.access_guard import StorageAccessGuard
from v5.storage.adapter import StorageAccessScope, StorageAdapter, StorageObjectMeta
from v5.storage.key_generator import generate_object_key, generate_tenant_prefix


class StorageService:
    def __init__(self, adapter: StorageAdapter, guard: StorageAccessGuard | None = None):
        self._adapter = adapter
        self._guard = guard or StorageAccessGuard()

    def upload_file(
        self,
        tenant_id: str,
        data_category: str,
        filename: str,
        data: bytes,
        mime_type: str | None = None,
    ) -> StorageObjectMeta:
        key = generate_object_key(tenant_id, data_category, filename)
        scope = StorageAccessScope(tenant_id=tenant_id, data_category=data_category)
        self._guard.check_write_access(key, scope)
        return self._adapter.put_object(
            key=key, data=data, mime_type=mime_type, tenant_id=tenant_id
        )

    def download_file(self, tenant_id: str, key: str) -> bytes:
        scope = StorageAccessScope(tenant_id=tenant_id)
        self._guard.check_read_access(key, scope)
        return self._adapter.get_object(key=key, tenant_id=tenant_id)

    def delete_file(self, tenant_id: str, key: str) -> None:
        scope = StorageAccessScope(tenant_id=tenant_id)
        self._guard.check_delete_access(key, scope)
        self._adapter.delete_object(key=key, tenant_id=tenant_id)

    def list_tenant_files(
        self,
        tenant_id: str,
        data_category: str | None = None,
        prefix: str | None = None,
    ) -> list[StorageObjectMeta]:
        if prefix:
            search_prefix = prefix
        elif data_category:
            search_prefix = f"{generate_tenant_prefix(tenant_id)}/{data_category}/"
        else:
            search_prefix = f"{generate_tenant_prefix(tenant_id)}/"

        scope = StorageAccessScope(tenant_id=tenant_id, data_category=data_category)
        self._guard.check_read_access(search_prefix.rstrip("/") + "/dummy", scope)
        return self._adapter.list_objects(prefix=search_prefix, tenant_id=tenant_id)

    def archive_object(self, tenant_id: str, key: str) -> None:
        scope = StorageAccessScope(tenant_id=tenant_id)
        self._guard.check_write_access(key, scope)
        self._adapter.set_lifecycle_state(key, "archived", tenant_id=tenant_id)

    def expire_object(self, tenant_id: str, key: str) -> None:
        scope = StorageAccessScope(tenant_id=tenant_id)
        self._guard.check_write_access(key, scope)
        self._adapter.set_lifecycle_state(key, "expired", tenant_id=tenant_id)
        self._adapter.set_retention_state(key, "deletable", tenant_id=tenant_id)

    def cleanup_expired(self, tenant_id: str) -> int:
        prefix = f"{generate_tenant_prefix(tenant_id)}/"
        all_objects = self._adapter.list_objects(prefix=prefix, tenant_id=tenant_id)
        expired = [
            obj
            for obj in all_objects
            if obj.lifecycle_state == "expired"
        ]
        count = 0
        for obj in expired:
            scope = StorageAccessScope(tenant_id=tenant_id)
            self._guard.check_delete_access(obj.storage_key, scope)
            self._adapter.delete_object(key=obj.storage_key, tenant_id=tenant_id)
            count += 1
        return count
