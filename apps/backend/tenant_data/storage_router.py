from contextlib import contextmanager
from typing import Callable

from sqlalchemy import text
from sqlalchemy.orm import Session, sessionmaker

from control_plane.schemas.database_targets import TenantDatabaseTargetModel


class StorageRouter:
    def __init__(
        self,
        control_plane_session_factory: Callable[[], Session] | sessionmaker[Session],
        tenant_data_engine=None,
    ):
        self._control_plane_session_factory = control_plane_session_factory
        self._tenant_data_engine = tenant_data_engine
        self._target_cache: dict[str, dict] = {}

    def resolve_target(self, tenant_id: str) -> dict:
        if tenant_id in self._target_cache:
            return self._target_cache[tenant_id]

        session = self._control_plane_session_factory()
        try:
            target = (
                session.query(TenantDatabaseTargetModel)
                .filter(
                    TenantDatabaseTargetModel.tenant_id == tenant_id,
                    TenantDatabaseTargetModel.status == "active",
                )
                .first()
            )
            if target is None:
                raise ValueError(
                    f"No active database target found for tenant {tenant_id}"
                )

            result = {
                "database_kind": target.database_kind,
                "connection_ref": target.connection_ref,
                "tenant_id": target.tenant_id,
            }
            self._target_cache[tenant_id] = result
            return result
        finally:
            session.close()

    def get_tenant_session(self, tenant_id: str) -> Session:
        _target = self.resolve_target(tenant_id)
        if self._tenant_data_engine is None:
            raise RuntimeError(
                "Tenant data engine not configured. "
                "Set tenant_data_engine on StorageRouter."
            )
        tenant_session_factory = sessionmaker(
            autocommit=False, autoflush=False, bind=self._tenant_data_engine
        )
        return tenant_session_factory()

    def set_tenant_context(self, db_session: Session, tenant_id: str) -> None:
        db_session.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, true)"),
            {"tid": tenant_id},
        )

    @contextmanager
    def route_transaction(self, tenant_id: str):
        session = self.get_tenant_session(tenant_id)
        try:
            self.set_tenant_context(session, tenant_id)
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def invalidate_cache(self, tenant_id: str | None = None) -> None:
        if tenant_id is not None:
            self._target_cache.pop(tenant_id, None)
        else:
            self._target_cache.clear()

