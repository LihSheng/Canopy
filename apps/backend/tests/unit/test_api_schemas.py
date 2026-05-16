import pytest

pytestmark = pytest.mark.api_schema

from api.schemas.anomalies import AnomalyDetailResponse, AnomalyItem, AnomalyListResponse
from api.schemas.common import ApiResponse
from api.schemas.dashboard import (
    ClaimTypeBreakdownItem,
    DashboardCommandViewResponse,
    DashboardSummaryResponse,
    DashboardTopDepartmentsResponse,
    DashboardTrendsResponse,
    MonthlyTrendItem,
    PeriodInfo,
    TopDepartmentItem,
)
from api.schemas.departments import (
    AiSummary,
    ClaimDetailItem,
    DepartmentDetailResponse,
    DepartmentItem,
    DepartmentListResponse,
    EmployeeContributionItem,
)
from api.schemas.exports import (
    ExportHistoryResponse,
    ExportJobResponse,
    ExportTriggerResponse,
    TriggerExportRequest,
)
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
        r = TriggerExportRequest(preset_name="Executive Summary")
        assert r.include_departments is None
        assert r.include_anomalies is None

    def test_export_trigger_response(self):
        r = ExportTriggerResponse(accepted=True, job_id="exp-1")
        assert r.accepted is True

    def test_export_job_response(self):
        j = ExportJobResponse(
            id="exp-1",
            status="completed",
            preset_name="Executive Summary",
            snapshot_id="snap-1",
            time_range="this_month",
            snapshot_timestamp="2026-05-16T10:00:00Z",
            started_at="2026-05-16T10:00:00Z",
            finished_at="2026-05-16T10:30:00Z",
            file_size_bytes=12500,
        )
        assert j.preset_name == "Executive Summary"

    def test_export_history_response(self):
        j = ExportJobResponse(id="exp-1", status="completed", preset_name="Executive Summary")
        h = ExportHistoryResponse(jobs=[j])
        assert len(h.jobs) == 1


class TestNewV2Schemas:
    def test_command_view_response(self):
        summary = DashboardSummaryResponse(
            total_payroll=1000.0, total_claims=500.0,
            period=PeriodInfo(year=2026, month=5),
            department_count=6, anomaly_count=3,
            last_updated="2026-05-16T10:00:00Z",
        )
        dept = TopDepartmentItem(
            id="d1", name="Engineering", total_spend=1000.0,
            payroll_spend=800.0, claims_spend=200.0, change_pct=5.5,
        )
        trend = MonthlyTrendItem(month="2026-05", payroll=1000.0, claims=200.0, total=1200.0)
        ct = ClaimTypeBreakdownItem(type="Travel", amount=500.0, count=10)
        a = AnomalyItem(
            id="a1", department_id="d1", department_name="Engineering",
            period="2026-05", description="Spike", severity="high", change_pct=15.0,
        )
        view = DashboardCommandViewResponse(
            summary=summary,
            departments=[dept],
            trends=[trend],
            claim_types=[ct],
            anomalies=[a],
        )
        assert view.summary.total_payroll == 1000.0
        assert len(view.departments) == 1
        assert len(view.trends) == 1
        assert len(view.claim_types) == 1
        assert len(view.anomalies) == 1

    def test_dashboard_trends_response(self):
        trend = MonthlyTrendItem(month="2026-05", payroll=1000.0, claims=200.0, total=1200.0)
        r = DashboardTrendsResponse(trends=[trend])
        assert len(r.trends) == 1

    def test_dashboard_top_departments_response(self):
        dept = TopDepartmentItem(
            id="d1", name="Engineering", total_spend=1000.0,
            payroll_spend=800.0, claims_spend=200.0, change_pct=5.5,
        )
        r = DashboardTopDepartmentsResponse(departments=[dept])
        assert len(r.departments) == 1

    def test_anomaly_list_response(self):
        a = AnomalyItem(
            id="a1", department_id="d1", department_name="Engineering",
            period="2026-05", description="Spike", severity="high", change_pct=15.0,
        )
        r = AnomalyListResponse(anomalies=[a], total=1)
        assert r.total == 1
        assert len(r.anomalies) == 1

    def test_department_list_response(self):
        d = DepartmentItem(
            id="d1", name="Engineering", total_spend=1000.0,
            payroll_spend=800.0, claims_spend=200.0, change_pct=5.5,
        )
        r = DepartmentListResponse(departments=[d], total=1)
        assert r.total == 1
        assert len(r.departments) == 1

    def test_department_detail_with_new_fields(self):
        d = DepartmentDetailResponse(
            id="d1", name="Engineering",
            payroll_spend=800.0, claims_spend=200.0, total_spend=1000.0,
            change_pct=5.5, employee_count=42,
        )
        assert d.attention_state is None
        assert d.ai_summary is None

    def test_department_detail_with_ai_summary(self):
        ai = AiSummary(summary_text="Stable spend", key_findings=["No anomalies"])
        d = DepartmentDetailResponse(
            id="d1", name="Engineering",
            payroll_spend=800.0, claims_spend=200.0, total_spend=1000.0,
            change_pct=5.5, employee_count=42,
            attention_state="attention",
            ai_summary=ai,
        )
        assert d.attention_state == "attention"
        assert d.ai_summary is not None
        assert d.ai_summary.summary_text == "Stable spend"
        assert d.ai_summary.key_findings == ["No anomalies"]
