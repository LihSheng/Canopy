import pytest

from object_storage.access_guard import StorageAccessGuard
from object_storage.adapter import StorageAccessScope
from object_storage.errors import StorageAccessError


class TestStorageAccessGuardRead:
    def test_same_tenant_allowed(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="tenant-A")
        result = guard.check_read_access("tenants/tenant-A/raw/file.csv", scope)
        assert result is True

    def test_different_tenant_denied(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="tenant-A")
        with pytest.raises(StorageAccessError, match="Access denied"):
            guard.check_read_access("tenants/tenant-B/raw/file.csv", scope)

    def test_no_tenant_prefix_denied(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="tenant-A")
        with pytest.raises(StorageAccessError, match="Access denied"):
            guard.check_read_access("other/file.csv", scope)

    def test_deeply_nested_path_same_tenant_allowed(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="t1")
        result = guard.check_read_access("tenants/t1/raw/uuid1/uuid2/nested/file.csv", scope)
        assert result is True

    def test_partial_tenant_match_denied(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="tenant-A")
        with pytest.raises(StorageAccessError, match="Access denied"):
            guard.check_read_access("tenants/tenant-AB/raw/file.csv", scope)


class TestStorageAccessGuardWrite:
    def test_same_tenant_allowed(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="tenant-A")
        result = guard.check_write_access("tenants/tenant-A/raw/file.csv", scope)
        assert result is True

    def test_different_tenant_denied(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="tenant-A")
        with pytest.raises(StorageAccessError, match="Access denied"):
            guard.check_write_access("tenants/tenant-B/raw/file.csv", scope)

    def test_admin_can_write_across_tenants(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="admin", is_admin=True)
        result = guard.check_write_access("tenants/tenant-B/raw/file.csv", scope)
        assert result is True

    def test_admin_write_to_own_tenant_allowed(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="tenant-A", is_admin=True)
        result = guard.check_write_access("tenants/tenant-A/raw/file.csv", scope)
        assert result is True


class TestStorageAccessGuardDelete:
    def test_same_tenant_deletable_allowed(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="tenant-A")
        result = guard.check_delete_access("tenants/tenant-A/raw/file.csv", scope)
        assert result is True

    def test_different_tenant_denied(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="tenant-A")
        with pytest.raises(StorageAccessError, match="Access denied"):
            guard.check_delete_access("tenants/tenant-B/raw/file.csv", scope)

    def test_admin_can_delete_across_tenants(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="admin", is_admin=True)
        result = guard.check_delete_access("tenants/tenant-B/raw/file.csv", scope)
        assert result is True

    def test_admin_delete_own_tenant_allowed(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="tenant-A", is_admin=True)
        result = guard.check_delete_access("tenants/tenant-A/raw/file.csv", scope)
        assert result is True

    def test_non_admin_cant_delete_other_tenant(self):
        guard = StorageAccessGuard()
        scope = StorageAccessScope(tenant_id="tenant-A", is_admin=False)
        with pytest.raises(StorageAccessError, match="Access denied"):
            guard.check_delete_access("tenants/tenant-B/raw/file.csv", scope)


class TestStorageAccessScopeDefaults:
    def test_default_values(self):
        scope = StorageAccessScope(tenant_id="t1")
        assert scope.is_admin is False
        assert scope.data_category is None

    def test_admin_scope(self):
        scope = StorageAccessScope(tenant_id="t1", is_admin=True)
        assert scope.is_admin is True

    def test_data_category_scope(self):
        scope = StorageAccessScope(tenant_id="t1", data_category="raw")
        assert scope.data_category == "raw"
