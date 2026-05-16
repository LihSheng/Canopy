from pydantic import BaseModel

from api.schemas.anomalies import AnomalyItem


class PeriodInfo(BaseModel):
    year: int
    month: int


class DashboardSummaryResponse(BaseModel):
    total_payroll: float
    total_claims: float
    period: PeriodInfo
    department_count: int
    anomaly_count: int
    last_updated: str


class TopDepartmentItem(BaseModel):
    id: str
    name: str
    total_spend: float
    payroll_spend: float
    claims_spend: float
    change_pct: float


class MonthlyTrendItem(BaseModel):
    month: str
    payroll: float
    claims: float
    total: float


class ClaimTypeBreakdownItem(BaseModel):
    type: str
    amount: float
    count: int


class DashboardTrendsResponse(BaseModel):
    trends: list[MonthlyTrendItem]


class DashboardTopDepartmentsResponse(BaseModel):
    departments: list[TopDepartmentItem]


class DashboardCommandViewResponse(BaseModel):
    summary: DashboardSummaryResponse
    departments: list[TopDepartmentItem]
    trends: list[MonthlyTrendItem]
    claim_types: list[ClaimTypeBreakdownItem]
    anomalies: list[AnomalyItem]
