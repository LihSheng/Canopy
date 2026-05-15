from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session


class SourceReader[T](ABC):
    """Contract every source reader must implement."""

    entity_type: str

    @abstractmethod
    def read(self, source_db: Session) -> list[T]: ...


# ---------------------------------------------------------------------------
# Source entity domain types
# ---------------------------------------------------------------------------


@dataclass
class SourceDepartment:
    source_key: str
    name: str
    parent_key: str | None = None
    status: str = "active"


@dataclass
class SourceEmployee:
    source_key: str
    full_name: str
    department_key: str
    cost_center_key: str | None = None


@dataclass
class SourceClaim:
    source_key: str
    employee_key: str
    department_key: str
    amount: float
    currency: str
    claim_type: str
    submitted_at: datetime
    status: str


@dataclass
class SourcePayroll:
    source_key: str
    employee_key: str
    department_key: str
    amount: float
    currency: str
    period_start: str
    period_end: str


@dataclass
class SourceCostCenter:
    source_key: str
    name: str
    department_key: str | None = None


@dataclass
class SourceBudgetCode:
    source_key: str
    name: str
    department_key: str | None = None


# ---------------------------------------------------------------------------
# Snapshot result types
# ---------------------------------------------------------------------------


@dataclass
class EntitySnapshot:
    """The result of reading one entity family during a sync run."""

    entity_type: str
    status: str  # "completed" | "failed"
    started_at: datetime
    completed_at: datetime | None = None
    row_count: int = 0
    error_message: str | None = None
    rows: list[Any] = field(default_factory=list)


@dataclass
class SyncResult:
    """Aggregate result of a full sync run."""

    snapshot_id: str
    status: str  # "completed" | "partial" | "failed"
    started_at: datetime
    completed_at: datetime | None = None
    snapshots: list[EntitySnapshot] = field(default_factory=list)
    error_message: str | None = None
