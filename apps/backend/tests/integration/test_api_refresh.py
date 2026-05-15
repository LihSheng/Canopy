import pytest

pytestmark = pytest.mark.api_schema

import time


class TestRefresh:
    def test_requires_auth(self, client):
        response = client.get("/api/refresh/current")
        assert response.status_code == 401

    def test_get_initial_status(self, client, auth_headers):
        response = client.get("/api/refresh/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "idle"
        assert data["last_refresh"] is None
        assert data["error_message"] is None

    def test_trigger_refresh(self, client, auth_headers):
        response = client.post("/api/refresh", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] is True
        assert data["job_id"] is not None
        assert len(data["job_id"]) > 0

    def test_get_job_after_trigger(self, client, auth_headers):
        trigger_response = client.post("/api/refresh", headers=auth_headers)
        job_id = trigger_response.json()["job_id"]

        response = client.get(
            f"/api/refresh/jobs/{job_id}", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == job_id
        assert data["trigger_type"] == "manual"
        assert data["status"] in ("pending", "running", "completed", "failed")

    def test_get_nonexistent_job(self, client, auth_headers):
        response = client.get(
            "/api/refresh/jobs/nonexistent-id", headers=auth_headers
        )
        assert response.status_code == 404

    def test_refresh_status_reflects_latest_job(self, client, auth_headers):
        client.post("/api/refresh", headers=auth_headers)

        deadline = time.monotonic() + 5.0
        final_status = None
        while time.monotonic() < deadline:
            response = client.get(
                "/api/refresh/current", headers=auth_headers
            )
            data = response.json()
            if data["status"] in ("completed", "failed", "running"):
                final_status = data
                break
            time.sleep(0.1)

        assert final_status is not None
        assert final_status["status"] in ("completed", "failed", "running")
