import os
import threading
import uuid

from common.executor import background
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from common.database import make_session
from backup.domain import BackupRun, BackupStatus, BackupType
from backup.errors import LifecycleStateError
from backup.lifecycle_validation import LifecycleValidator
from backup.policy_manager import BackupPolicyManager
from control_plane.audit_service import AuditService
from control_plane.config_repository import ConfigRepository
from control_plane.tenant_repository import TenantRepository


class BackupEngine:
    def __init__(
        self,
        tenant_repository_class: type[TenantRepository],
        config_repository_class: type[ConfigRepository],
        audit_service_class: type[AuditService],
        db_session_factory: Callable[[], Session],
        backup_dir: str = "./backups",
    ):
        self._tenant_repo_cls = tenant_repository_class
        self._config_repo_cls = config_repository_class
        self._audit_service_cls = audit_service_class
        self._db_session_factory = db_session_factory
        self._backup_dir = backup_dir
        self._runs: dict[str, BackupRun] = {}
        self._lock = threading.Lock()

    def create_backup(
        self, tenant_id: str, backup_type: BackupType = BackupType.FULL
    ) -> BackupRun:
        run = BackupRun(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            backup_type=backup_type,
            status=BackupStatus.PENDING,
        )
        with self._lock:
            self._runs[run.id] = run

        background.run(
            target=self._execute_backup,
            args=(run.id,),
            name=f"backup-{run.id}",
        )
        return run

    def _execute_backup(self, run_id: str) -> None:
        with self._lock:
            run = self._runs.get(run_id)
        if run is None:
            return

        run.status = BackupStatus.RUNNING
        run.started_at = datetime.now(timezone.utc)

        session = make_session(self._db_session_factory)
        try:
            tenant_repo = self._tenant_repo_cls(session)
            tenant = tenant_repo.get_tenant_by_id(run.tenant_id)
            if tenant is None:
                self._fail_run(run, "Tenant not found", session)
                return

            errors = LifecycleValidator.can_backup(tenant)
            if errors:
                self._fail_run(run, "; ".join(errors), session)
                return

            run.snapshot_ref = f"pg_dump:{run.tenant_id}:{run.id}"

            run.status = BackupStatus.COMPLETED
            run.finished_at = datetime.now(timezone.utc)

            audit_service = self._audit_service_cls(session)
            audit_service.record_event(
                tenant_id=run.tenant_id,
                actor_user_id="system",
                event_type="backup.created",
                payload={
                    "backup_run_id": run.id,
                    "backup_type": run.backup_type.value,
                    "size_bytes": run.size_bytes,
                },
            )
        except Exception as e:
            self._fail_run(run, str(e), session)
        finally:
            session.close()

    def _fail_run(self, run: BackupRun, message: str, session: Session) -> None:
        run.status = BackupStatus.FAILED
        run.finished_at = datetime.now(timezone.utc)
        run.error_message = message
        try:
            audit_service = self._audit_service_cls(session)
            audit_service.record_event(
                tenant_id=run.tenant_id,
                actor_user_id="system",
                event_type="backup.failed",
                payload={
                    "backup_run_id": run.id,
                    "error_message": message,
                },
            )
        except Exception:
            pass

    def list_backups(self, tenant_id: str) -> list[BackupRun]:
        with self._lock:
            return [r for r in self._runs.values() if r.tenant_id == tenant_id]

    def get_backup(self, backup_id: str) -> BackupRun | None:
        with self._lock:
            return self._runs.get(backup_id)

    def _run_retention_cleanup(self, tenant_id: str) -> int:
        session = self._db_session_factory()
        try:
            policy_manager = BackupPolicyManager(self._config_repo_cls(session))
            policy = policy_manager.get_policy(tenant_id)
        finally:
            session.close()

        with self._lock:
            tenant_backups = sorted(
                [r for r in self._runs.values() if r.tenant_id == tenant_id],
                key=lambda r: r.started_at or datetime.min.replace(tzinfo=timezone.utc),
            )
            removed = 0
            if len(tenant_backups) > policy.max_backups:
                to_remove = tenant_backups[: len(tenant_backups) - policy.max_backups]
                for run in to_remove:
                    if run.snapshot_ref and os.path.exists(run.snapshot_ref):
                        os.remove(run.snapshot_ref)
                    del self._runs[run.id]
                    removed += 1

            cutoff = datetime.now(timezone.utc)
            for run in list(self._runs.values()):
                if run.tenant_id != tenant_id:
                    continue
                if run.finished_at is None:
                    continue
                age_days = (cutoff - run.finished_at).days
                if age_days > policy.retention_days:
                    if run.snapshot_ref and os.path.exists(run.snapshot_ref):
                        os.remove(run.snapshot_ref)
                    del self._runs[run.id]
                    removed += 1

            return removed

