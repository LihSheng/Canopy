from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class MonthlyDepartmentSpend:
    id: str
    snapshot_id: str
    department_id: str
    month: str
    payroll_total: float = 0.0
    claims_total: float = 0.0
    total: float = 0.0
    claim_count: int = 0


@dataclass
class MonthlyEmployeeSpend:
    id: str
    snapshot_id: str
    employee_id: str
    department_id: str
    month: str
    payroll_total: float = 0.0
    claims_total: float = 0.0
    total: float = 0.0


@dataclass
class MonthlyClaimTypeSpend:
    id: str
    snapshot_id: str
    department_id: str | None
    claim_type: str
    month: str
    amount: float = 0.0
    claim_count: int = 0


@dataclass
class DepartmentRanking:
    snapshot_id: str
    department_id: str
    department_name: str
    month: str
    total_spend: float = 0.0
    payroll_spend: float = 0.0
    claims_spend: float = 0.0
    rank: int = 0
    change_pct: float = 0.0


@dataclass
class DepartmentMoMDelta:
    snapshot_id: str
    department_id: str
    current_month: str
    previous_month: str
    current_total: float = 0.0
    previous_total: float = 0.0
    total_change: float = 0.0
    total_change_pct: float = 0.0


@dataclass
class DashboardSummaryCache:
    snapshot_id: str
    year: int
    month: int
    total_payroll: float = 0.0
    total_claims: float = 0.0
    department_count: int = 0
    anomaly_count: int = 0
    created_at: str = ""


@dataclass
class EmployeeContributionSummary:
    employee_id: str
    employee_name: str
    department_id: str
    department_name: str
    month: str
    payroll: float = 0.0
    claims: float = 0.0
    total: float = 0.0


@dataclass
class ClaimDetailSummary:
    claim_id: str
    employee_name: str
    department_id: str
    department_name: str
    claim_type: str
    amount: float
    claim_date: str


# Read models for analytics service layer (returned to API routes)
@dataclass
class DashboardSummary:
    total_payroll: float
    total_claims: float
    year: int
    month: int
    department_count: int
    anomaly_count: int
    last_updated: str
    snapshot_id: str = ""


@dataclass
class MonthlyTrend:
    month: str
    payroll: float
    claims: float
    total: float


@dataclass
class TopDepartment:
    id: str
    name: str
    total_spend: float
    payroll_spend: float
    claims_spend: float
    change_pct: float


@dataclass
class ClaimTypeBreakdown:
    type: str
    amount: float
    count: int


@dataclass
class DepartmentSummary:
    id: str
    name: str
    total_spend: float
    payroll_spend: float
    claims_spend: float
    change_pct: float


@dataclass
class DepartmentDetail:
    id: str
    name: str
    total_spend: float
    payroll_spend: float
    claims_spend: float
    change_pct: float
    employee_count: int
    attention_state: str | None = None
    ai_summary: str | None = None


@dataclass
class EmployeeContribution:
    id: str
    name: str
    department: str
    payroll: float
    claims: float
    total: float


@dataclass
class DepartmentClaimType:
    type: str
    amount: float
    count: int


@dataclass
class ClaimDetail:
    id: str
    employee_name: str
    department: str
    type: str
    amount: float
    date: str
