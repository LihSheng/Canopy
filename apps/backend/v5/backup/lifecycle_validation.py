from datetime import datetime, timezone

from v5.control_plane.schemas.tenants import TenantModel


class LifecycleValidator:
    @staticmethod
    def can_backup(tenant: TenantModel) -> list[str]:
        errors: list[str] = []
        if tenant.lifecycle_state == "deleted":
            errors.append("Cannot backup a deleted tenant")
        if tenant.lifecycle_state == "pending":
            errors.append("Cannot backup a pending tenant (no data)")
        return errors

    @staticmethod
    def can_restore(tenant: TenantModel) -> list[str]:
        errors: list[str] = []
        if tenant.lifecycle_state == "deleted":
            errors.append("Cannot restore a deleted tenant")
        return errors

    @staticmethod
    def can_clone(tenant: TenantModel) -> list[str]:
        errors: list[str] = []
        if tenant.lifecycle_state == "deleted":
            errors.append("Cannot clone a deleted tenant")
        return errors

    @staticmethod
    def is_restorable_from_archive(
        tenant: TenantModel, archive_date: datetime, retention_days: int
    ) -> bool:
        now = datetime.now(timezone.utc)
        if archive_date.tzinfo is None:
            archive_date = archive_date.replace(tzinfo=timezone.utc)
        delta = now - archive_date
        return delta.days <= retention_days
