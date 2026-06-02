from dataclasses import dataclass
from datetime import datetime


@dataclass
class FeatureFlag:
    """Server-backed global feature flag that affects all users.

    Managed by internal Admin role only. v1 supports on/off toggles.
    """

    flag_key: str
    description: str
    enabled: bool
    id: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None
