from dataclasses import dataclass, field


@dataclass
class FactBundle:
    snapshot_id: str
    current_month: str
    previous_month: str | None
    total_payroll: float = 0.0
    total_claims: float = 0.0
    department_count: int = 0
    anomaly_count: int = 0
    top_departments: list["TopDepartmentFact"] = field(default_factory=list)
    anomalies: list["AnomalyFact"] = field(default_factory=list)
    claim_type_breakdown: list["ClaimTypeFact"] = field(default_factory=list)
    department_rankings: list["DepartmentRankingFact"] = field(default_factory=list)


@dataclass
class TopDepartmentFact:
    id: str
    name: str
    total_spend: float = 0.0
    payroll_spend: float = 0.0
    claims_spend: float = 0.0
    change_pct: float = 0.0


@dataclass
class AnomalyFact:
    department_name: str
    severity: str
    description: str
    change_pct: float = 0.0


@dataclass
class ClaimTypeFact:
    type: str
    amount: float = 0.0
    count: int = 0


@dataclass
class DepartmentRankingFact:
    name: str
    total_spend: float = 0.0


@dataclass
class InsightSummary:
    id: str
    snapshot_id: str
    current_month: str
    summary_text: str = ""
    recommendations: list[str] = field(default_factory=list)
    key_findings: list[str] = field(default_factory=list)
    is_fallback: bool = False
    generated_at: str = ""
    anomaly_count: int = 0
    department_count: int = 0
    total_payroll: float = 0.0
    total_claims: float = 0.0
