from pydantic import BaseModel


class InsightItem(BaseModel):
    id: str
    snapshot_id: str
    current_month: str
    summary_text: str
    recommendations: list[str]
    key_findings: list[str]
    is_fallback: bool
    generated_at: str
    anomaly_count: int
    department_count: int
    total_payroll: float
    total_claims: float
