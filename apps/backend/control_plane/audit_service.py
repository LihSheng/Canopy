import json
import uuid
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from control_plane.schemas.audit import AuditEventModel, ImpersonationSessionModel


class AuditService:
    def __init__(self, db: Session):
        self._db = db

    def record_event(
        self,
        tenant_id: str | None,
        actor_user_id: str,
        event_type: str,
        payload: dict | None = None,
    ) -> AuditEventModel:
        event = AuditEventModel(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            event_type=event_type,
            event_payload_json=json.dumps(payload) if payload else None,
        )
        self._db.add(event)
        self._db.commit()
        self._db.refresh(event)
        return event

    def record_impersonation_start(self, admin_user_id: str, tenant_id: str, reason: str) -> ImpersonationSessionModel:
        session = ImpersonationSessionModel(
            id=str(uuid.uuid4()),
            platform_admin_user_id=admin_user_id,
            tenant_id=tenant_id,
            reason=reason,
            status="active",
        )
        self._db.add(session)
        self._db.commit()
        self._db.refresh(session)
        return session

    def record_impersonation_end(self, session_id: str) -> ImpersonationSessionModel:
        session = self._db.query(ImpersonationSessionModel).filter(ImpersonationSessionModel.id == session_id).first()
        if session is None:
            raise ValueError(f"Impersonation session {session_id} not found")
        session.finished_at = datetime.now(UTC)
        session.status = "ended"
        self._db.commit()
        self._db.refresh(session)
        return session

    def get_audit_events(self, tenant_id: str | None = None, limit: int = 100) -> list[AuditEventModel]:
        q = self._db.query(AuditEventModel).order_by(AuditEventModel.created_at.desc())
        if tenant_id is not None:
            q = q.filter(AuditEventModel.tenant_id == tenant_id)
        return q.limit(limit).all()
