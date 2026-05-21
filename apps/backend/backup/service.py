from backup.backup_engine import BackupEngine
from backup.clone_engine import CloneEngine
from backup.domain import BackupRun, BackupStatus, BackupType, CloneRun, RestoreRun
from backup.errors import BackupInProgressError
from backup.policy_manager import BackupPolicyManager
from backup.restore_engine import RestoreEngine


class BackupService:
    def __init__(
        self,
        backup_engine: BackupEngine,
        restore_engine: RestoreEngine,
        clone_engine: CloneEngine,
        policy_manager: BackupPolicyManager,
    ):
        self._backup_engine = backup_engine
        self._restore_engine = restore_engine
        self._clone_engine = clone_engine
        self._policy_manager = policy_manager

    def request_backup(self, tenant_id: str, backup_type: BackupType = BackupType.FULL) -> BackupRun:
        return self._backup_engine.create_backup(tenant_id, backup_type)

    def request_restore(self, tenant_id: str, backup_run_id: str) -> RestoreRun:
        return self._restore_engine.create_restore(tenant_id, backup_run_id)

    def request_clone(self, source_tenant_id: str, target_tenant_name: str) -> CloneRun:
        return self._clone_engine.create_clone(source_tenant_id, target_tenant_name)

    def get_backup_status(self, tenant_id: str) -> dict:
        backups = self._backup_engine.list_backups(tenant_id)
        restores = self._restore_engine.list_restores(tenant_id)
        last_backup = backups[-1] if backups else None
        last_restore = restores[-1] if restores else None
        pending_jobs = sum(1 for r in backups + restores if r.status in (BackupStatus.PENDING, BackupStatus.RUNNING))
        return {
            "last_backup": (
                {
                    "id": last_backup.id,
                    "status": last_backup.status.value,
                    "started_at": (last_backup.started_at.isoformat() if last_backup.started_at else None),
                }
                if last_backup
                else None
            ),
            "last_restore": (
                {
                    "id": last_restore.id,
                    "status": last_restore.status.value,
                    "started_at": (last_restore.started_at.isoformat() if last_restore.started_at else None),
                }
                if last_restore
                else None
            ),
            "pending_jobs": pending_jobs,
        }

    def get_backup_history(self, tenant_id: str) -> list[BackupRun]:
        return self._backup_engine.list_backups(tenant_id)

    def cancel_backup(self, backup_id: str) -> None:
        backup = self._backup_engine.get_backup(backup_id)
        if backup is None:
            return
        if backup.status != BackupStatus.PENDING:
            raise BackupInProgressError(f"Cannot cancel backup in '{backup.status.value}' state")
        backup.status = BackupStatus.FAILED
        backup.error_message = "Cancelled by user"

    def is_pitr_supported(self, tenant_id: str) -> bool:
        policy = self._policy_manager.get_policy(tenant_id)
        return policy.pitr_enabled
