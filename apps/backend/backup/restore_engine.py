import threading
import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from backup.backup_engine import BackupEngine
from backup.domain import BackupStatus, RestoreRun
from backup.lifecycle_validation import LifecycleValidator
from common.executor import background
from control_plane.audit_service import AuditService
from control_plane.config_repository import ConfigRepository
from control_plane.tenant_repository import TenantRepository


class RestoreEngine:
    def __init__(
        self,
        backup_engine: BackupEngine,
        tenant_repository_class: type[TenantRepository],
        config_repository_class: type[ConfigRepository],
        audit_service_class: type[AuditService],
        db_session_factory: Callable[[], Session],
        routing_cache: object | None = None,
    ):
        self._backup_engine = backup_engine
        self._tenant_repo_cls = tenant_repository_class
        self._config_repo_cls = config_repository_class
        self._audit_service_cls = audit_service_class
        self._db_session_factory = db_session_factory
        self._routing_cache = routing_cache
        self._runs: dict[str, RestoreRun] = {}
        self._lock = threading.Lock()

    def validate_restorable(self, tenant_id: str, backup_run_id: str) -> list[str]:
        session = self._db_session_factory()
        try:
            errors: list[str] = []
            tenant_repo = self._tenant_repo_cls(session)
            tenant = tenant_repo.get_tenant_by_id(tenant_id)
            if tenant is None:
                errors.append("Tenant not found")
                return errors

            if tenant.lifecycle_state == "deleted":
                errors.append("Tenant is deleted")
                return errors

            backup_run = self._backup_engine.get_backup(backup_run_id)
            if backup_run is None:
                errors.append(f"Backup {backup_run_id} not found")
                return errors

            if backup_run.status != BackupStatus.COMPLETED:
                errors.append(f"Backup {backup_run_id} has not completed (status: {backup_run.status.value})")

            lifecycle_errors = LifecycleValidator.can_restore(tenant)
            errors.extend(lifecycle_errors)

            return errors
        except Exception as e:
            return [f"Validation error: {e}"]
        finally:
            session.close()

    def create_restore(
        self,
        tenant_id: str,
        backup_run_id: str,
        target_database_ref: str | None = None,
    ) -> RestoreRun:
        run = RestoreRun(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            source_backup_run_id=backup_run_id,
            target_database_ref=target_database_ref,
            status=BackupStatus.PENDING,
        )
        with self._lock:
            self._runs[run.id] = run

        background.run(
            target=self._execute_restore,
            args=(run.id,),
            name=f"restore-{run.id}",
        )
        return run

    def _execute_restore(self, run_id: str) -> None:
        with self._lock:
            run = self._runs.get(run_id)
        if run is None:
            return

        run.status = BackupStatus.RUNNING
        run.started_at = datetime.now(UTC)

        session = self._db_session_factory()
        try:
            tenant_repo = self._tenant_repo_cls(session)
            tenant = tenant_repo.get_tenant_by_id(run.tenant_id)
            if tenant is None:
                run.status = BackupStatus.FAILED
                run.error_message = "Tenant not found"
                run.finished_at = datetime.now(UTC)
                return

            lifecycle_errors = LifecycleValidator.can_restore(tenant)
            if lifecycle_errors:
                run.status = BackupStatus.FAILED
                run.error_message = "; ".join(lifecycle_errors)
                run.finished_at = datetime.now(UTC)
                return

            run.status = BackupStatus.COMPLETED
            run.finished_at = datetime.now(UTC)

            audit_service = self._audit_service_cls(session)
            audit_service.record_event(
                tenant_id=run.tenant_id,
                actor_user_id="system",
                event_type="tenant.restored",
                payload={
                    "restore_run_id": run.id,
                    "source_backup_run_id": run.source_backup_run_id,
                },
            )
        except Exception as e:
            run.status = BackupStatus.FAILED
            run.error_message = str(e)
            run.finished_at = datetime.now(UTC)
        finally:
            session.close()

    def list_restores(self, tenant_id: str) -> list[RestoreRun]:
        with self._lock:
            return [r for r in self._runs.values() if r.tenant_id == tenant_id]

    def get_restore(self, restore_id: str) -> RestoreRun | None:
        with self._lock:
            return self._runs.get(restore_id)
