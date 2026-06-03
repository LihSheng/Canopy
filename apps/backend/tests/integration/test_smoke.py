import pytest

from common.executor import SameThreadRunner

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.usefixtures("seed_analytics_data"),
]


@pytest.fixture(autouse=True)
def _sync_refresh_background(monkeypatch):
    import refresh.service as refresh_service

    monkeypatch.setattr(refresh_service, "background", SameThreadRunner())


class TestSmoke:
    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        body = response.json()
        assert body["status"] == "ok"

    def test_login_and_dashboard_summary(self, client, auth_headers):
        response = client.get("/api/dashboard/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total_payroll"] > 0
        assert data["department_count"] > 0

    def test_department_drill_down(self, client, auth_headers):
        response = client.get("/api/departments", headers=auth_headers)
        assert response.status_code == 200
        depts = response.json()
        assert isinstance(depts, list)
        assert len(depts) > 0

        dept_id = depts[0]["id"]
        detail = client.get(f"/api/departments/{dept_id}", headers=auth_headers)
        assert detail.status_code == 200
        assert detail.json()["id"] == dept_id

    def test_refresh_request_and_status(self, client, auth_headers):
        trigger = client.post("/api/refresh", headers=auth_headers)
        assert trigger.status_code == 200
        job = trigger.json()
        assert job["accepted"] is True
        assert job["job_id"]

        status = client.get("/api/refresh/current", headers=auth_headers)
        assert status.status_code == 200
        assert status.json()["status"] in (
            "idle",
            "pending",
            "running",
            "completed",
            "failed",
        )

    def test_export_request(self, client, auth_headers):
        response = client.post(
            "/api/exports/executive-summary",
            headers=auth_headers,
            json={"include_departments": True, "include_anomalies": True},
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        assert response.content[:2] == b"PK"
