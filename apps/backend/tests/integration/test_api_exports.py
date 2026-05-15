class TestExports:
    def test_requires_auth(self, client):
        response = client.post("/api/exports/executive-summary", json={})
        assert response.status_code == 401

    def test_request_export(self, client, auth_headers):
        response = client.post(
            "/api/exports/executive-summary",
            json={"include_departments": True, "include_anomalies": True},
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["accepted"] is True
        assert data["status"] == "queued"
