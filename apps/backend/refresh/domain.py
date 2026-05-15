from dataclasses import dataclass
from datetime import datetime
from typing import Literal

RefreshJobStatus = Literal["pending", "running", "completed", "failed"]
RefreshStage = Literal[
    "extract_source",
    "normalize_ontology",
    "rebuild_aggregates",
    "detect_anomalies",
    "generate_insights",
    "publish_snapshot",
]
DataSnapshotStatus = Literal["current", "archived"]

STAGE_ORDER: list[RefreshStage] = [
    "extract_source",
    "normalize_ontology",
    "rebuild_aggregates",
    "detect_anomalies",
    "generate_insights",
    "publish_snapshot",
]


@dataclass
class RefreshJob:
    id: str
    status: RefreshJobStatus = "pending"
    current_stage: RefreshStage | None = None
    snapshot_id: str | None = None
    trigger_type: str = "manual"
    requested_by_user_id: str | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_message: str | None = None


@dataclass
class DataSnapshot:
    id: str
    refresh_job_id: str
    status: DataSnapshotStatus
    created_at: str
