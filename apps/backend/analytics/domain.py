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
