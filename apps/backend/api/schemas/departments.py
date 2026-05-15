from pydantic import BaseModel


class DepartmentItem(BaseModel):
    id: str
    name: str
    total_spend: float
    payroll_spend: float
    claims_spend: float
    change_pct: float


class DepartmentDetailResponse(BaseModel):
    id: str
    name: str
    payroll_spend: float
    claims_spend: float
    total_spend: float
    change_pct: float
    employee_count: int


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
