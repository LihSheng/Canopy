from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class BackupType(Enum):
    FULL = "full"
    SCHEMA_ONLY = "schema_only"
    PITR = "pitr"


class BackupStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class BackupPolicy:
    tenant_id: str
    backup_type: BackupType = BackupType.FULL
    schedule_cron: str = "0 2 * * *"
    retention_days: int = 30
    max_backups: int = 10
    pitr_enabled: bool = True
    enabled: bool = True


@dataclass
class BackupRun:
    id: str
    tenant_id: str
    backup_type: BackupType
    status: BackupStatus = BackupStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    snapshot_ref: str | None = None
    size_bytes: int = 0
    error_message: str | None = None


@dataclass
class RestoreRun:
    id: str
    tenant_id: str
    source_backup_run_id: str
    target_database_ref: str | None = None
    status: BackupStatus = BackupStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None


@dataclass
class CloneRun:
    id: str
    source_tenant_id: str
    target_tenant_id: str | None = None
    target_tenant_name: str | None = None
    status: BackupStatus = BackupStatus.PENDING
    started_at: datetime | None = None
    finished_at: datetime | None = None
    new_database_target_ref: str | None = None
    error_message: str | None = None
