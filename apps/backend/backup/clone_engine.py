import threading
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backup.domain import BackupStatus, CloneRun
from backup.lifecycle_validation import LifecycleValidator
from common.executor import background
from control_plane.audit_service import AuditService
from control_plane.config_repository import ConfigRepository
from control_plane.tenant_repository import TenantRepository


class CloneEngine:
    def __init__(
        self,
        tenant_repository_class: type[TenantRepository],
        config_repository_class: type[ConfigRepository],
        audit_service_class: type[AuditService],
        db_session_factory: Callable[[], Session],
        lifecycle_service: object | None = None,
        routing_cache: object | None = None,
    ):
        self._tenant_repo_cls = tenant_repository_class
        self._config_repo_cls = config_repository_class
        self._audit_service_cls = audit_service_class
        self._db_session_factory = db_session_factory
        self._lifecycle_service = lifecycle_service
        self._routing_cache = routing_cache
        self._runs: dict[str, CloneRun] = {}
        self._lock = threading.Lock()

    def create_clone(self, source_tenant_id: str, target_tenant_name: str) -> CloneRun:
        run = CloneRun(
            id=str(uuid.uuid4()),
            source_tenant_id=source_tenant_id,
            target_tenant_name=target_tenant_name,
            status=BackupStatus.PENDING,
        )
        with self._lock:
            self._runs[run.id] = run

        background.run(
            target=self._execute_clone,
            args=(run.id,),
            name=f"clone-{run.id}",
        )
        return run

    def _execute_clone(self, run_id: str) -> None:
        with self._lock:
            run = self._runs.get(run_id)
        if run is None:
            return

        run.status = BackupStatus.RUNNING
        run.started_at = datetime.now(UTC)

        session = self._db_session_factory()
        try:
            tenant_repo = self._tenant_repo_cls(session)
            tenant = tenant_repo.get_tenant_by_id(run.source_tenant_id)
            if tenant is None:
                self._fail_run(run, "Source tenant not found", session)
                return

            lifecycle_errors = LifecycleValidator.can_clone(tenant)
            if lifecycle_errors:
                self._fail_run(run, "; ".join(lifecycle_errors), session)
                return

            run.status = BackupStatus.COMPLETED
            run.finished_at = datetime.now(UTC)
        except Exception as e:
            self._fail_run(run, str(e), session)
        finally:
            session.close()

    def _fail_run(self, run: CloneRun, message: str, session: Session) -> None:
        run.status = BackupStatus.FAILED
        run.finished_at = datetime.now(UTC)
        run.error_message = message
        try:
            audit_service = self._audit_service_cls(session)
            audit_service.record_event(
                tenant_id=run.source_tenant_id,
                actor_user_id="system",
                event_type="clone.failed",
                payload={"clone_run_id": run.id, "error_message": message},
            )
        except Exception:
            pass

    def list_clones(self, source_tenant_id: str | None = None) -> list[CloneRun]:
        with self._lock:
            if source_tenant_id is None:
                return list(self._runs.values())
            return [r for r in self._runs.values() if r.source_tenant_id == source_tenant_id]

    def get_clone(self, clone_id: str) -> CloneRun | None:
        with self._lock:
            return self._runs.get(clone_id)
