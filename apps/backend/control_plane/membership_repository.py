import uuid

from sqlalchemy.orm import Session, joinedload

from control_plane.schemas.memberships import TenantMembershipModel
from control_plane.schemas.tenants import TenantModel


class MembershipRepository:
    def __init__(self, db: Session):
        self._db = db

    def add_member(
        self, user_id: str, tenant_id: str, role: str = "member"
    ) -> TenantMembershipModel:
        membership = TenantMembershipModel(
            id=str(uuid.uuid4()),
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
        )
        self._db.add(membership)
        self._db.commit()
        self._db.refresh(membership)
        return membership

    def remove_member(self, user_id: str, tenant_id: str) -> None:
        membership = (
            self._db.query(TenantMembershipModel)
            .filter(
                TenantMembershipModel.user_id == user_id,
                TenantMembershipModel.tenant_id == tenant_id,
            )
            .first()
        )
        if membership is not None:
            self._db.delete(membership)
            self._db.commit()

    def get_membership(
        self, user_id: str, tenant_id: str
    ) -> TenantMembershipModel | None:
        return (
            self._db.query(TenantMembershipModel)
            .filter(
                TenantMembershipModel.user_id == user_id,
                TenantMembershipModel.tenant_id == tenant_id,
            )
            .first()
        )

    def get_user_tenants(self, user_id: str) -> list[TenantMembershipModel]:
        return (
            self._db.query(TenantMembershipModel)
            .filter(TenantMembershipModel.user_id == user_id)
            .options(joinedload(TenantMembershipModel.tenant_id))
            .all()
        )

    def get_tenant_members(self, tenant_id: str) -> list[TenantMembershipModel]:
        return (
            self._db.query(TenantMembershipModel)
            .filter(TenantMembershipModel.tenant_id == tenant_id)
            .all()
        )

    def update_role(
        self, user_id: str, tenant_id: str, new_role: str
    ) -> TenantMembershipModel:
        membership = (
            self._db.query(TenantMembershipModel)
            .filter(
                TenantMembershipModel.user_id == user_id,
                TenantMembershipModel.tenant_id == tenant_id,
            )
            .first()
        )
        if membership is None:
            raise ValueError("Membership not found")
        membership.role = new_role
        self._db.commit()
        self._db.refresh(membership)
        return membership

