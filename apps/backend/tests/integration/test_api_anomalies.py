import pytest

from anomalies.service import detect_anomalies

pytestmark = pytest.mark.api_schema


class TestAnomalies:
    def test_requires_auth(self, client):
        response = client.get("/api/anomalies")
        assert response.status_code == 401

    def test_list_anomalies_with_seeded_data(
        self, client, auth_headers, db_session, seed_analytics_data
    ):
        detect_anomalies(
            db_session,
            snapshot_id="test-snapshot-001",
            current_month="2026-05",
            previous_month="2026-04",
        )

        response = client.get("/api/anomalies", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
        assert "id" in data[0]
        assert "severity" in data[0]
        assert "department_name" in data[0]
        assert "change_pct" in data[0]

    def test_list_anomalies_v2_contract_shape(
        self, client, auth_headers, db_session, seed_analytics_data
    ):
        detect_anomalies(
            db_session,
            snapshot_id="test-snapshot-001",
            current_month="2026-05",
            previous_month="2026-04",
        )

        response = client.get("/api/anomalies", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            for field in ["id", "department_id", "department_name", "period",
                           "description", "severity", "change_pct"]:
                assert field in item, f"Missing field in anomaly item: {field}"

    def test_list_anomalies_filter_by_department(
        self, client, auth_headers, db_session, seed_analytics_data
    ):
        detect_anomalies(
            db_session,
            snapshot_id="test-snapshot-001",
            current_month="2026-05",
            previous_month="2026-04",
        )

        response = client.get(
            "/api/anomalies?department_id=dept-1", headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        for item in data:
            assert item["department_id"] == "dept-1"

    def test_anomaly_detail_with_seeded_data(
        self, client, auth_headers, db_session, seed_analytics_data
    ):
        detect_anomalies(
            db_session,
            snapshot_id="test-snapshot-001",
            current_month="2026-05",
            previous_month="2026-04",
        )

        response_list = client.get("/api/anomalies", headers=auth_headers)
        anomalies = response_list.json()
        assert len(anomalies) > 0

        first_id = anomalies[0]["id"]
        response = client.get(f"/api/anomalies/{first_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == first_id
        assert "baseline_value" in data
        assert "observed_value" in data
        assert "driver_details" in data

    def test_anomaly_not_found(self, client, auth_headers):
        response = client.get("/api/anomalies/nonexistent-999", headers=auth_headers)
        assert response.status_code == 404
