class TestAnomalies:
    def test_requires_auth(self, client):
        response = client.get("/api/anomalies")
        assert response.status_code == 401

    def test_list_anomalies(self, client, auth_headers):
        response = client.get("/api/anomalies", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 3
        assert data[0]["id"] == "anom-1"
        assert "severity" in data[0]
        assert "department_name" in data[0]

    def test_anomaly_detail(self, client, auth_headers):
        response = client.get("/api/anomalies/anom-1", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "anom-1"
        assert data["severity"] == "high"
        assert "baseline_value" in data
        assert "observed_value" in data
        assert "driver_details" in data

    def test_anomaly_not_found(self, client, auth_headers):
        response = client.get("/api/anomalies/anom-999", headers=auth_headers)
        assert response.status_code == 404
