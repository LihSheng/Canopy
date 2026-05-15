
from api.schemas.anomalies import AnomalyDetailResponse, AnomalyItem
from api.schemas.common import ApiResponse
from api.schemas.dashboard import (
    ClaimTypeBreakdownItem,
    DashboardSummaryResponse,
    MonthlyTrendItem,
    PeriodInfo,
    TopDepartmentItem,
)
from api.schemas.departments import (
    ClaimDetailItem,
    DepartmentDetailResponse,
    DepartmentItem,
    EmployeeContributionItem,
)
from api.schemas.exports import ExportRequest, ExportResponse
from api.schemas.refresh import RefreshJobResponse, RefreshRequestResponse, RefreshStatusResponse


class TestResponseEnvelope:
    def test_envelope_success_with_data(self):
        resp = ApiResponse(success=True, data={"key": "value"})
        assert resp.success is True
        assert resp.data == {"key": "value"}
        assert resp.error is None

    def test_envelope_error(self):
        resp = ApiResponse(success=False, error="Something went wrong")
        assert resp.success is False
        assert resp.data is None
        assert resp.error == "Something went wrong"

    def test_envelope_with_meta(self):
        resp = ApiResponse(success=True, data=None, meta={"snapshot_id": "snap-1"})
        assert resp.meta == {"snapshot_id": "snap-1"}


class TestDashboardSchemas:
    def test_summary_valid(self):
        data = DashboardSummaryResponse(
            total_payroll=1000.0,
            total_claims=500.0,
            period=PeriodInfo(year=2026, month=5),
            department_count=10,
            anomaly_count=2,
            last_updated="2026-05-15T10:00:00Z",
        )
        assert data.total_payroll == 1000.0

    def test_period_info_valid(self):
        period = PeriodInfo(year=2026, month=12)
        assert period.year == 2026
        assert period.month == 12

    def test_top_department_valid(self):
        dept = TopDepartmentItem(
            id="d1", name="Engineering", total_spend=1000.0,
            payroll_spend=800.0, claims_spend=200.0, change_pct=5.5,
        )
        assert dept.id == "d1"

    def test_monthly_trend_valid(self):
        trend = MonthlyTrendItem(month="2026-05", payroll=1000.0, claims=200.0, total=1200.0)
        assert trend.month == "2026-05"

    def test_claim_type_breakdown_valid(self):
        item = ClaimTypeBreakdownItem(type="Travel", amount=500.0, count=10)
        assert item.type == "Travel"


class TestDepartmentSchemas:
    def test_department_item_valid(self):
        d = DepartmentItem(
            id="d1", name="Eng", total_spend=1000.0,
            payroll_spend=800.0, claims_spend=200.0, change_pct=1.0,
        )
        assert d.id == "d1"

    def test_department_detail_valid(self):
        d = DepartmentDetailResponse(
            id="d1", name="Eng", payroll_spend=800.0,
            claims_spend=200.0, total_spend=1000.0,
            change_pct=1.0, employee_count=42,
        )
        assert d.employee_count == 42

    def test_employee_contribution_valid(self):
        e = EmployeeContributionItem(
            id="e1", name="Alice", department="Eng",
            payroll=5000.0, claims=200.0, total=5200.0,
        )
        assert e.name == "Alice"

    def test_claim_detail_valid(self):
        c = ClaimDetailItem(
            id="c1", employee_name="Alice", department="Eng",
            type="Travel", amount=200.0, date="2026-05-01",
        )
        assert c.date == "2026-05-01"


class TestAnomalySchemas:
    def test_anomaly_item_valid(self):
        a = AnomalyItem(
            id="a1", department_id="d1", department_name="Eng",
            period="2026-05", description="Spike", severity="high",
            change_pct=15.0,
        )
        assert a.severity == "high"

    def test_anomaly_detail_valid(self):
        a = AnomalyDetailResponse(
            id="a1", department_id="d1", department_name="Eng", period="2026-05",
            description="Spike", severity="high", change_pct=15.0,
            baseline_value=1000.0, observed_value=1150.0, delta_value=150.0,
            delta_percent=15.0, driver_details=["Hiring"],
        )
        assert a.delta_value == 150.0


class TestRefreshSchemas:
    def test_refresh_request_response(self):
        r = RefreshRequestResponse(accepted=True, job_id="j1")
        assert r.accepted is True
        assert r.job_id == "j1"

    def test_refresh_status_response(self):
        r = RefreshStatusResponse(
            status="completed",
            last_refresh="2026-05-15T10:00:00Z",
            last_attempt="2026-05-15T09:59:00Z",
        )
        assert r.status == "completed"

    def test_refresh_job_response(self):
        r = RefreshJobResponse(job_id="j1", trigger_type="manual", status="completed")
        assert r.job_id == "j1"


class TestExportSchemas:
    def test_export_request_defaults(self):
        r = ExportRequest()
        assert r.include_departments is True
        assert r.include_anomalies is True

    def test_export_response(self):
        r = ExportResponse(accepted=True, status="queued")
        assert r.accepted is True
