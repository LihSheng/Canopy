from dataclasses import dataclass, field


@dataclass
class DepartmentExportRow:
    rank: int
    department_name: str
    total_spend: float = 0.0
    payroll_spend: float = 0.0
    claims_spend: float = 0.0
    change_pct: float = 0.0


@dataclass
class AnomalyExportRow:
    department_name: str
    period: str
    description: str
    severity: str = "low"
    change_pct: float = 0.0


@dataclass
class MonthlyTrendExportRow:
    month: str
    payroll: float = 0.0
    claims: float = 0.0
    total: float = 0.0


@dataclass
class ExportPayload:
    snapshot_id: str
    generated_at: str
    departments: list[DepartmentExportRow] = field(default_factory=list)
    anomalies: list[AnomalyExportRow] = field(default_factory=list)
    summary_payroll: float = 0.0
    summary_claims: float = 0.0
    department_count: int = 0
    anomaly_count: int = 0
    period_label: str = ""
    trends: list[MonthlyTrendExportRow] = field(default_factory=list)
