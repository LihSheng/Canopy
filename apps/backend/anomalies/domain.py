from dataclasses import dataclass, field
from typing import Protocol

from analytics.domain import MonthlyDepartmentSpend


@dataclass
class AnomalyOutput:
    id: str
    snapshot_id: str
    anomaly_type: str
    target_entity_type: str
    target_entity_id: str
    month_key: str
    baseline_value: float = 0.0
    observed_value: float = 0.0
    delta_value: float = 0.0
    delta_percent: float = 0.0
    severity: str = "low"
    driver_details: list[str] = field(default_factory=list)
    description: str = ""


class AnomalyRule(Protocol):
    anomaly_type: str

    def __call__(
        self,
        snapshot_id: str,
        current_spends: list[MonthlyDepartmentSpend],
        previous_spends: list[MonthlyDepartmentSpend],
    ) -> list[AnomalyOutput]: ...
