# ruff: noqa: E501
from api.schemas.dashboard import (
    ClaimTypeBreakdownItem,
    DashboardSummaryResponse,
    MonthlyTrendItem,
    PeriodInfo,
    TopDepartmentItem,
)


def get_dashboard_summary() -> DashboardSummaryResponse:
    return DashboardSummaryResponse(
        total_payroll=1245000.00,
        total_claims=287350.50,
        period=PeriodInfo(year=2026, month=5),
        department_count=12,
        anomaly_count=3,
        last_updated="2026-05-15T10:30:00Z",
    )


def get_monthly_trends() -> list[MonthlyTrendItem]:
    return [
        MonthlyTrendItem(month="2025-11", payroll=1180000.00, claims=265000.00, total=1445000.00),
        MonthlyTrendItem(month="2025-12", payroll=1210000.00, claims=272000.00, total=1482000.00),
        MonthlyTrendItem(month="2026-01", payroll=1195000.00, claims=258000.00, total=1453000.00),
        MonthlyTrendItem(month="2026-02", payroll=1205000.00, claims=275000.00, total=1480000.00),
        MonthlyTrendItem(month="2026-03", payroll=1220000.00, claims=280000.00, total=1500000.00),
        MonthlyTrendItem(month="2026-04", payroll=1235000.00, claims=283000.00, total=1518000.00),
        MonthlyTrendItem(month="2026-05", payroll=1245000.00, claims=287350.50, total=1532350.50),
    ]


def get_top_departments() -> list[TopDepartmentItem]:
    return [
        TopDepartmentItem(id="dept-1", name="Engineering", total_spend=485000.00, payroll_spend=420000.00, claims_spend=65000.00, change_pct=3.2),
        TopDepartmentItem(id="dept-2", name="Sales", total_spend=380000.00, payroll_spend=310000.00, claims_spend=70000.00, change_pct=-1.5),
        TopDepartmentItem(id="dept-3", name="Marketing", total_spend=275000.00, payroll_spend=230000.00, claims_spend=45000.00, change_pct=8.7),
        TopDepartmentItem(id="dept-4", name="Operations", total_spend=210000.00, payroll_spend=180000.00, claims_spend=30000.00, change_pct=1.1),
        TopDepartmentItem(id="dept-5", name="Finance", total_spend=182350.50, payroll_spend=155000.00, claims_spend=27350.50, change_pct=-0.8),
    ]


def get_claim_type_breakdown() -> list[ClaimTypeBreakdownItem]:
    return [
        ClaimTypeBreakdownItem(type="Travel", amount=98000.00, count=145),
        ClaimTypeBreakdownItem(type="Meals", amount=65400.00, count=320),
        ClaimTypeBreakdownItem(type="Office Supplies", amount=42350.50, count=89),
        ClaimTypeBreakdownItem(type="Training", amount=38500.00, count=24),
        ClaimTypeBreakdownItem(type="Equipment", amount=28100.00, count=15),
        ClaimTypeBreakdownItem(type="Other", amount=15000.00, count=42),
    ]
