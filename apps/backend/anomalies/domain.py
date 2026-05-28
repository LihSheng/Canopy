from dataclasses import dataclass, field


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
