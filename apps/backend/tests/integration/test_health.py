from fastapi.testclient import TestClient

from app import app


class TestHealthIntegration:
    def test_api_health_endpoint(self):
        client = TestClient(app)
        response = client.get("/api/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
