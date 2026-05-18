import json

from backup.domain import BackupPolicy, BackupType
from control_plane.config_repository import ConfigRepository


_BACKUP_POLICY_CONFIG_KEY = "backup_policy"


class BackupPolicyManager:
    def __init__(self, config_repository: ConfigRepository):
        self._config_repo = config_repository

    def get_policy(self, tenant_id: str) -> BackupPolicy:
        config = self._config_repo.get_config(tenant_id, _BACKUP_POLICY_CONFIG_KEY)
        if config is None:
            return self.get_default_policy(tenant_id)
        try:
            data = json.loads(config.config_value_json)
        except (json.JSONDecodeError, TypeError):
            return self.get_default_policy(tenant_id)
        return BackupPolicy(
            tenant_id=tenant_id,
            backup_type=BackupType(data.get("backup_type", "full")),
            schedule_cron=data.get("schedule_cron", "0 2 * * *"),
            retention_days=int(data.get("retention_days", 30)),
            max_backups=int(data.get("max_backups", 10)),
            pitr_enabled=bool(data.get("pitr_enabled", True)),
            enabled=bool(data.get("enabled", True)),
        )

    def save_policy(self, tenant_id: str, policy: BackupPolicy) -> None:
        data = {
            "backup_type": policy.backup_type.value,
            "schedule_cron": policy.schedule_cron,
            "retention_days": policy.retention_days,
            "max_backups": policy.max_backups,
            "pitr_enabled": policy.pitr_enabled,
            "enabled": policy.enabled,
        }
        self._config_repo.set_config(
            tenant_id, _BACKUP_POLICY_CONFIG_KEY, json.dumps(data)
        )

    def get_default_policy(self, tenant_id: str) -> BackupPolicy:
        return BackupPolicy(
            tenant_id=tenant_id,
            backup_type=BackupType.FULL,
            schedule_cron="0 2 * * *",
            retention_days=30,
            max_backups=10,
            pitr_enabled=True,
            enabled=True,
        )

    def is_backup_enabled(self, tenant_id: str) -> bool:
        policy = self.get_policy(tenant_id)
        return policy.enabled

