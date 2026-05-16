from pydantic import BaseModel


class AnomalyItem(BaseModel):
    id: str
    department_id: str
    department_name: str
    period: str
    description: str
    severity: str
    change_pct: float


class AnomalyDetailResponse(BaseModel):
    id: str
    department_id: str
    department_name: str
    period: str
    description: str
    severity: str
    change_pct: float
    baseline_value: float
    observed_value: float
    delta_value: float
    delta_percent: float
    driver_details: list[str]


class AnomalyListResponse(BaseModel):
    anomalies: list[AnomalyItem]
    total: int
