import uuid

from sqlalchemy.orm import Session

from control_plane.schemas.tenants import TenantModel


class TenantRepository:
    def __init__(self, db: Session):
        self._db = db

    def create_tenant(self, name: str, slug: str) -> TenantModel:
        tenant = TenantModel(
            id=str(uuid.uuid4()),
            tenant_uuid=str(uuid.uuid4()),
            name=name,
            slug=slug,
        )
        self._db.add(tenant)
        self._db.commit()
        self._db.refresh(tenant)
        return tenant

    def get_tenant_by_id(self, tenant_id: str) -> TenantModel | None:
        return self._db.query(TenantModel).filter(TenantModel.id == tenant_id).first()

    def get_tenant_by_slug(self, slug: str) -> TenantModel | None:
        return self._db.query(TenantModel).filter(TenantModel.slug == slug).first()

    def list_tenants(self, status_filter: str | None = None) -> list[TenantModel]:
        q = self._db.query(TenantModel)
        if status_filter is not None:
            q = q.filter(TenantModel.lifecycle_state == status_filter)
        return q.all()

    def update_lifecycle_state(self, tenant_id: str, new_state: str) -> TenantModel:
        tenant = self._db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        tenant.lifecycle_state = new_state
        self._db.commit()
        self._db.refresh(tenant)
        return tenant

    def delete_tenant(self, tenant_id: str) -> None:
        tenant = self._db.query(TenantModel).filter(TenantModel.id == tenant_id).first()
        if tenant is None:
            return
        self._db.delete(tenant)
        self._db.commit()
