import json

from backup.domain import BackupPolicy, BackupType
from backup.policy_manager import BackupPolicyManager
from control_plane.config_repository import ConfigRepository


class TestDefaultPolicy:
    def test_default_policy_has_sensible_values(self, db_session):
        repo = ConfigRepository(db_session)
        manager = BackupPolicyManager(repo)
        policy = manager.get_default_policy("t-1")

        assert policy.backup_type == BackupType.FULL
        assert policy.schedule_cron == "0 2 * * *"
        assert policy.retention_days == 30
        assert policy.max_backups == 10
        assert policy.pitr_enabled is True
        assert policy.enabled is True

    def test_get_policy_returns_default_when_not_configured(self, db_session):
        repo = ConfigRepository(db_session)
        manager = BackupPolicyManager(repo)
        policy = manager.get_policy("t-nonexistent")

        assert policy.tenant_id == "t-nonexistent"
        assert policy.backup_type == BackupType.FULL
        assert policy.retention_days == 30


class TestSaveAndLoadPolicy:
    def test_save_and_load_policy_roundtrip(self, db_session):
        repo = ConfigRepository(db_session)
        manager = BackupPolicyManager(repo)

        original = BackupPolicy(
            tenant_id="t-1",
            backup_type=BackupType.PITR,
            schedule_cron="0 6 * * *",
            retention_days=60,
            max_backups=20,
            pitr_enabled=True,
            enabled=True,
        )
        manager.save_policy("t-1", original)
        loaded = manager.get_policy("t-1")

        assert loaded.backup_type == BackupType.PITR
        assert loaded.schedule_cron == "0 6 * * *"
        assert loaded.retention_days == 60
        assert loaded.max_backups == 20
        assert loaded.pitr_enabled is True
        assert loaded.enabled is True

    def test_save_policy_creates_config_record(self, db_session):
        repo = ConfigRepository(db_session)
        manager = BackupPolicyManager(repo)

        policy = BackupPolicy(
            tenant_id="t-2",
            backup_type=BackupType.SCHEMA_ONLY,
            retention_days=14,
            max_backups=5,
        )
        manager.save_policy("t-2", policy)

        config = repo.get_config("t-2", "backup_policy")
        assert config is not None
        data = json.loads(config.config_value_json)
        assert data["backup_type"] == "schema_only"
        assert data["retention_days"] == 14
        assert data["max_backups"] == 5

    def test_save_policy_updates_existing(self, db_session):
        repo = ConfigRepository(db_session)
        manager = BackupPolicyManager(repo)

        policy1 = BackupPolicy(tenant_id="t-3", retention_days=7)
        manager.save_policy("t-3", policy1)

        policy2 = BackupPolicy(tenant_id="t-3", retention_days=90)
        manager.save_policy("t-3", policy2)

        loaded = manager.get_policy("t-3")
        assert loaded.retention_days == 90


class TestPolicyValidation:
    def test_retention_days_must_be_positive(self, db_session):
        policy = BackupPolicy(tenant_id="t-1", retention_days=30)
        assert policy.retention_days > 0

    def test_max_backups_must_be_positive(self, db_session):
        policy = BackupPolicy(tenant_id="t-1", max_backups=10)
        assert policy.max_backups > 0


class TestDisabledPolicy:
    def test_disabled_policy_prevents_backup(self, db_session):
        repo = ConfigRepository(db_session)
        manager = BackupPolicyManager(repo)

        policy = BackupPolicy(tenant_id="t-1", enabled=False)
        manager.save_policy("t-1", policy)

        assert manager.is_backup_enabled("t-1") is False

    def test_enabled_policy_allows_backup(self, db_session):
        repo = ConfigRepository(db_session)
        manager = BackupPolicyManager(repo)

        policy = BackupPolicy(tenant_id="t-1", enabled=True)
        manager.save_policy("t-1", policy)

        assert manager.is_backup_enabled("t-1") is True

    def test_is_backup_enabled_defaults_to_true(self, db_session):
        repo = ConfigRepository(db_session)
        manager = BackupPolicyManager(repo)

        assert manager.is_backup_enabled("t-new") is True

