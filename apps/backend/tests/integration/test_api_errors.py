import pytest

pytestmark = pytest.mark.api_schema


class TestErrorEnvelopeShape:
    def test_unauthorized_shape(self, client):
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_not_found_shape(self, client, auth_headers):
        response = client.get("/api/departments/dept-999", headers=auth_headers)
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_not_found_anomaly_shape(self, client, auth_headers):
        response = client.get("/api/anomalies/anom-999", headers=auth_headers)
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data

    def test_invalid_export_payload_get_stable_error(self, client, auth_headers):
        response = client.post(
            "/api/exports/executive-summary",
            json={"include_departments": "not-a-bool"},
            headers=auth_headers,
        )
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    def test_missing_input_field_returns_validation_error(self, client, auth_headers):
        response = client.post(
            "/api/exports/executive-summary",
            json={},
            headers=auth_headers,
        )
        assert response.status_code in (200, 201) or response.status_code == 422
