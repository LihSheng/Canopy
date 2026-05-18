from datetime import datetime, timedelta, timezone

import pytest

from v5.backup.lifecycle_validation import LifecycleValidator
from v5.control_plane.schemas.tenants import TenantModel


def _make_tenant(lifecycle_state: str) -> TenantModel:
    return TenantModel(
        id=f"t-{lifecycle_state}",
        tenant_uuid=f"tuuid-{lifecycle_state}",
        name=f"{lifecycle_state.capitalize()} Tenant",
        slug=f"{lifecycle_state}-tenant",
        lifecycle_state=lifecycle_state,
    )


class TestCanBackup:
    def test_active_tenant_backup_ok(self):
        tenant = _make_tenant("active")
        errors = LifecycleValidator.can_backup(tenant)
        assert errors == []

    def test_suspended_tenant_backup_ok(self):
        tenant = _make_tenant("suspended")
        errors = LifecycleValidator.can_backup(tenant)
        assert errors == []

    def test_archived_tenant_backup_ok(self):
        tenant = _make_tenant("archived")
        errors = LifecycleValidator.can_backup(tenant)
        assert errors == []

    def test_pending_tenant_backup_not_ok(self):
        tenant = _make_tenant("pending")
        errors = LifecycleValidator.can_backup(tenant)
        assert len(errors) > 0
        assert any("pending" in e.lower() for e in errors)

    def test_deleted_tenant_backup_not_ok(self):
        tenant = _make_tenant("deleted")
        errors = LifecycleValidator.can_backup(tenant)
        assert len(errors) > 0
        assert any("deleted" in e.lower() for e in errors)


class TestCanRestore:
    def test_active_tenant_restore_ok(self):
        tenant = _make_tenant("active")
        errors = LifecycleValidator.can_restore(tenant)
        assert errors == []

    def test_suspended_tenant_restore_ok(self):
        tenant = _make_tenant("suspended")
        errors = LifecycleValidator.can_restore(tenant)
        assert errors == []

    def test_archived_tenant_restore_ok(self):
        tenant = _make_tenant("archived")
        errors = LifecycleValidator.can_restore(tenant)
        assert errors == []

    def test_pending_tenant_restore_ok(self):
        tenant = _make_tenant("pending")
        errors = LifecycleValidator.can_restore(tenant)
        assert errors == []

    def test_deleted_tenant_restore_not_ok(self):
        tenant = _make_tenant("deleted")
        errors = LifecycleValidator.can_restore(tenant)
        assert len(errors) > 0
        assert any("deleted" in e.lower() for e in errors)


class TestCanClone:
    def test_active_tenant_clone_ok(self):
        tenant = _make_tenant("active")
        errors = LifecycleValidator.can_clone(tenant)
        assert errors == []

    def test_suspended_tenant_clone_ok(self):
        tenant = _make_tenant("suspended")
        errors = LifecycleValidator.can_clone(tenant)
        assert errors == []

    def test_archived_tenant_clone_ok(self):
        tenant = _make_tenant("archived")
        errors = LifecycleValidator.can_clone(tenant)
        assert errors == []

    def test_pending_tenant_clone_ok_by_lifecycle(self):
        tenant = _make_tenant("pending")
        errors = LifecycleValidator.can_clone(tenant)
        assert errors == []

    def test_deleted_tenant_clone_not_ok(self):
        tenant = _make_tenant("deleted")
        errors = LifecycleValidator.can_clone(tenant)
        assert len(errors) > 0
        assert any("deleted" in e.lower() for e in errors)


class TestArchiveRetention:
    def test_within_retention_window_ok(self):
        tenant = _make_tenant("archived")
        archive_date = datetime.now(timezone.utc) - timedelta(days=10)
        result = LifecycleValidator.is_restorable_from_archive(
            tenant, archive_date, retention_days=30
        )
        assert result is True

    def test_past_retention_window_not_ok(self):
        tenant = _make_tenant("archived")
        archive_date = datetime.now(timezone.utc) - timedelta(days=60)
        result = LifecycleValidator.is_restorable_from_archive(
            tenant, archive_date, retention_days=30
        )
        assert result is False

    def test_exactly_at_boundary_ok(self):
        tenant = _make_tenant("archived")
        archive_date = datetime.now(timezone.utc) - timedelta(days=30)
        result = LifecycleValidator.is_restorable_from_archive(
            tenant, archive_date, retention_days=30
        )
        assert result is True
