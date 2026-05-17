import io

import pytest
from fastapi.testclient import TestClient


class TestUploadEndpoint:
    def test_upload_success(self, client: TestClient, auth_headers):
        file_bytes = b"name,amount\nAlice,100\nBob,200"
        response = client.post(
            "/api/v3/ingestion/uploads",
            files={"file": ("payroll.csv", io.BytesIO(file_bytes), "text/csv")},
            data={"source_profile": "herdhr", "dataset_type": "payroll"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "uploaded"
        assert data["file_name"] == "payroll.csv"
        assert data["file_size"] == len(file_bytes)
        assert len(data["checksum"]) == 64
        assert "upload_id" in data

    def test_upload_unauthorized(self, client: TestClient):
        response = client.post(
            "/api/v3/ingestion/uploads",
            files={"file": ("test.csv", io.BytesIO(b"a,b\n1,2"), "text/csv")},
            data={"source_profile": "herdhr", "dataset_type": "payroll"},
        )
        assert response.status_code == 401

    def test_upload_invalid_extension(self, client: TestClient, auth_headers):
        response = client.post(
            "/api/v3/ingestion/uploads",
            files={"file": ("test.pdf", io.BytesIO(b"fake"), "application/pdf")},
            data={"source_profile": "herdhr", "dataset_type": "payroll"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "Unsupported file type" in response.text

    def test_upload_oversized(self, client: TestClient, auth_headers):
        large = b"x" * (51 * 1024 * 1024)
        response = client.post(
            "/api/v3/ingestion/uploads",
            files={"file": ("large.xlsx", io.BytesIO(large), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"source_profile": "herdhr", "dataset_type": "payroll"},
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "exceeds maximum size" in response.text


class TestGetUploadEndpoint:
    def test_get_upload_returns_record(self, client: TestClient, auth_headers):
        file_bytes = b"x,y\n1,2"
        upload_resp = client.post(
            "/api/v3/ingestion/uploads",
            files={"file": ("data.csv", io.BytesIO(file_bytes), "text/csv")},
            data={"source_profile": "herdhr", "dataset_type": "payroll"},
            headers=auth_headers,
        )
        upload_id = upload_resp.json()["upload_id"]

        response = client.get(f"/api/v3/ingestion/uploads/{upload_id}", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["upload_id"] == upload_id
        assert data["file_name"] == "data.csv"

    def test_get_upload_not_found(self, client: TestClient, auth_headers):
        response = client.get("/api/v3/ingestion/uploads/nonexistent-id", headers=auth_headers)
        assert response.status_code == 404
