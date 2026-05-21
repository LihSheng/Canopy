from object_storage.adapter import StorageAccessScope
from object_storage.errors import StorageAccessError


class StorageAccessGuard:
    def check_read_access(self, key: str, scope: StorageAccessScope) -> bool:
        if not key.startswith(f"tenants/{scope.tenant_id}/"):
            raise StorageAccessError(key, f"Key does not belong to tenant '{scope.tenant_id}'")
        return True

    def check_write_access(self, key: str, scope: StorageAccessScope) -> bool:
        if not key.startswith(f"tenants/{scope.tenant_id}/"):
            if scope.is_admin:
                return True
            raise StorageAccessError(key, f"Key does not belong to tenant '{scope.tenant_id}'")
        return True

    def check_delete_access(self, key: str, scope: StorageAccessScope) -> bool:
        if not key.startswith(f"tenants/{scope.tenant_id}/"):
            if scope.is_admin:
                return True
            raise StorageAccessError(key, f"Key does not belong to tenant '{scope.tenant_id}'")
        return True
