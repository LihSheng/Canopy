from pydantic import BaseModel


class DepartmentItem(BaseModel):
    id: str
    name: str
    total_spend: float
    payroll_spend: float
    claims_spend: float
    change_pct: float


class DepartmentListResponse(BaseModel):
    departments: list[DepartmentItem]
    total: int


class AiSummary(BaseModel):
    summary_text: str = ""
    key_findings: list[str] = []


class DepartmentDetailResponse(BaseModel):
    id: str
    name: str
    payroll_spend: float
    claims_spend: float
    total_spend: float
    change_pct: float
    employee_count: int
    attention_state: str | None = None
    ai_summary: str | None = None


class EmployeeContributionItem(BaseModel):
    id: str
    name: str
    department: str
    payroll: float
    claims: float
    total: float


class ClaimDetailItem(BaseModel):
    id: str
    employee_name: str
    department: str
    type: str
    amount: float
    date: str


class DepartmentClaimTypeItem(BaseModel):
    type: str
    amount: float
    count: int
