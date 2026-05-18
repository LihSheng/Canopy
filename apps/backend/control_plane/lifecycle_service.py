from sqlalchemy.orm import Session

from common.errors import ValidationError
from cache.hooks import after_tenant_restored, after_tenant_suspended
from control_plane.audit_service import AuditService
from control_plane.tenant_repository import TenantRepository


class LifecycleService:
    def __init__(self, db: Session):
        self._db = db
        self._tenant_repo = TenantRepository(db)
        self._audit = AuditService(db)

    def suspend_tenant(self, tenant_id: str, actor_user_id: str):
        tenant = self._tenant_repo.get_tenant_by_id(tenant_id)
        if tenant is None:
            raise ValidationError("Tenant not found")
        if tenant.lifecycle_state not in ("active",):
            raise ValidationError(
                f"Cannot suspend tenant in '{tenant.lifecycle_state}' state"
            )
        tenant.lifecycle_state = "suspended"
        self._db.commit()
        self._audit.record_event(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            event_type="tenant.suspended",
            payload={"tenant_id": tenant_id, "tenant_name": tenant.name},
        )
        after_tenant_suspended(tenant_id)
        return tenant

    def restore_tenant(self, tenant_id: str, actor_user_id: str):
        tenant = self._tenant_repo.get_tenant_by_id(tenant_id)
        if tenant is None:
            raise ValidationError("Tenant not found")
        if tenant.lifecycle_state not in ("suspended", "archived"):
            raise ValidationError(
                f"Cannot restore tenant in '{tenant.lifecycle_state}' state"
            )
        tenant.lifecycle_state = "active"
        self._db.commit()
        self._audit.record_event(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            event_type="tenant.restored",
            payload={"tenant_id": tenant_id, "tenant_name": tenant.name},
        )
        after_tenant_restored(tenant_id)
        return tenant

    def archive_tenant(self, tenant_id: str, actor_user_id: str):
        tenant = self._tenant_repo.get_tenant_by_id(tenant_id)
        if tenant is None:
            raise ValidationError("Tenant not found")
        if tenant.lifecycle_state not in ("active", "suspended"):
            raise ValidationError(
                f"Cannot archive tenant in '{tenant.lifecycle_state}' state"
            )
        tenant.lifecycle_state = "archived"
        self._db.commit()
        self._audit.record_event(
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            event_type="tenant.archived",
            payload={"tenant_id": tenant_id, "tenant_name": tenant.name},
        )
        return tenant

