from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from api.services.dashboard import get_dashboard_command_view

pytestmark = pytest.mark.business_rule


class TestGetDashboardCommandView:
    def test_returns_composite_dashboard_payload(self):
        summary = SimpleNamespace(
            total_payroll=1000.0,
            total_claims=200.0,
            year=2026,
            month=5,
            department_count=3,
            anomaly_count=1,
            last_updated="2026-05-15T10:00:00Z",
        )
        department = SimpleNamespace(
            id="dept-1",
            name="Engineering",
            total_spend=700.0,
            payroll_spend=500.0,
            claims_spend=200.0,
            change_pct=4.0,
        )
        trend = SimpleNamespace(month="2026-05", payroll=1000.0, claims=200.0, total=1200.0)
        claim_type = SimpleNamespace(type="Travel", amount=200.0, count=2)
        anomaly = {
            "id": "anom-1",
            "department_id": "dept-1",
            "department_name": "Engineering",
            "period": "2026-05",
            "description": "Spike",
            "severity": "high",
            "change_pct": 12.5,
        }

        with (
            patch("api.services.dashboard.get_dashboard_summary", return_value=summary),
            patch("api.services.dashboard.get_top_departments", return_value=[department]),
            patch("api.services.dashboard.get_monthly_trends", return_value=[trend]),
            patch("api.services.dashboard.get_claim_type_breakdown", return_value=[claim_type]),
            patch("api.services.dashboard.get_anomalies_list", return_value=[anomaly]),
        ):
            result = get_dashboard_command_view(MagicMock())

        assert result.summary.total_payroll == 1000.0
        assert result.summary.period.year == 2026
        assert result.departments[0].id == "dept-1"
        assert result.trends[0].month == "2026-05"
        assert result.claim_types[0].type == "Travel"
        assert result.anomalies[0].id == "anom-1"
