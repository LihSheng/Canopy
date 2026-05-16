import pytest

pytestmark = pytest.mark.api_schema


@pytest.mark.usefixtures("seed_analytics_data")
class TestDashboardSummary:
    def test_requires_auth(self, client):
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 401

    def test_returns_summary(self, client, auth_headers):
        response = client.get("/api/dashboard/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_payroll"] > 0
        assert data["total_claims"] > 0
        assert data["period"]["year"] == 2026
        assert data["department_count"] > 0
        assert "last_updated" in data

    def test_returns_trends(self, client, auth_headers):
        response = client.get("/api/dashboard/trends", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert data[0]["month"] == "2025-11"
        assert "payroll" in data[0]
        assert "claims" in data[0]
        assert "total" in data[0]

    def test_returns_top_departments(self, client, auth_headers):
        response = client.get("/api/dashboard/top-departments", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 5
        assert data[0]["id"] == "dept-1"
        assert "name" in data[0]
        assert "change_pct" in data[0]

    def test_returns_claim_types(self, client, auth_headers):
        response = client.get("/api/dashboard/claim-types", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 6
        assert data[0]["type"] == "Travel"
        assert "amount" in data[0]
        assert "count" in data[0]

    def test_command_view_returns_composite_response(self, client, auth_headers):
        response = client.get("/api/dashboard/command-view", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()

        assert "summary" in data
        assert "departments" in data
        assert "trends" in data
        assert "claim_types" in data
        assert "anomalies" in data

        summary = data["summary"]
        assert summary["total_payroll"] > 0
        assert summary["total_claims"] > 0
        assert summary["period"]["year"] == 2026

        departments = data["departments"]
        assert isinstance(departments, list)
        assert len(departments) == 5
        assert departments[0]["id"] == "dept-1"

        trends = data["trends"]
        assert isinstance(trends, list)
        assert len(trends) > 0
        assert "payroll" in trends[0]

        claim_types = data["claim_types"]
        assert isinstance(claim_types, list)
        assert len(claim_types) == 6

        anomalies = data["anomalies"]
        assert isinstance(anomalies, list)

    def test_command_view_requires_auth(self, client):
        response = client.get("/api/dashboard/command-view")
        assert response.status_code == 401
