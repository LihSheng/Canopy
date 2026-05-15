class TestRefresh:
    def test_requires_auth(self, client):
        response = client.get("/api/refresh/current")
        assert response.status_code == 401

    def test_get_current_status(self, client, auth_headers):
        response = client.get("/api/refresh/current", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["last_refresh"] is not None
        assert data["error_message"] is None

    def test_trigger_refresh(self, client, auth_headers):
        response = client.post("/api/refresh", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] is True
        assert data["job_id"] is not None

    def test_get_job(self, client, auth_headers):
        response = client.get("/api/refresh/jobs/job-001", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["job_id"] == "job-001"
        assert data["status"] == "completed"
