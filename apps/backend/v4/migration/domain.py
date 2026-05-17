from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MigratableUpload:
    upload_id: str
    file_name: str
    dataset_type: str
    source_profile: str
    upload_status: str
    workflow_status: str | None = None
    snapshot_count: int = 0
    created_at: datetime | None = None
