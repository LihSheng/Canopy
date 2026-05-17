import io

import openpyxl
import pytest
from fastapi.testclient import TestClient


def _make_xlsx(rows: list[list]) -> io.BytesIO:
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


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


class TestMappingEndpoints:
    def _upload(self, client: TestClient, auth_headers) -> str:
        resp = client.post(
            "/api/v3/ingestion/uploads",
            files={"file": ("data.csv", io.BytesIO(b"name,amount\nAlice,100"), "text/csv")},
            data={"source_profile": "herdhr", "dataset_type": "payroll"},
            headers=auth_headers,
        )
        return resp.json()["upload_id"]

    def test_save_and_retrieve_mappings(self, client: TestClient, auth_headers):
        upload_id = self._upload(client, auth_headers)
        decisions = [
            {"source_column_name": "name", "target_field_name": "employee_name", "confirmed": True, "overridden_by_user": False},
            {"source_column_name": "amount", "target_field_name": "salary", "confirmed": True, "overridden_by_user": True},
        ]

        save_resp = client.post(
            f"/api/v3/ingestion/uploads/{upload_id}/mapping",
            json=decisions,
            headers=auth_headers,
        )
        assert save_resp.status_code == 200
        saved = save_resp.json()
        assert len(saved) == 2
        assert saved[0]["source_column_name"] == "name"
        assert saved[0]["target_field_name"] == "employee_name"
        assert saved[1]["overridden_by_user"] is True

        get_resp = client.get(
            f"/api/v3/ingestion/uploads/{upload_id}/mapping",
            headers=auth_headers,
        )
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["upload_id"] == upload_id
        assert len(data["decisions"]) == 2
        assert data["decisions"][0]["source_column_name"] == "name"

    def test_get_mappings_fallback_to_suggestions(self, client: TestClient, auth_headers):
        buf = _make_xlsx([["name", "amount"], ["Alice", 100], ["Bob", 200]])
        resp = client.post(
            "/api/v3/ingestion/uploads",
            files={"file": ("data.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"source_profile": "herdhr", "dataset_type": "payroll"},
            headers=auth_headers,
        )
        upload_id = resp.json()["upload_id"]

        resp = client.get(
            f"/api/v3/ingestion/uploads/{upload_id}/mapping",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["decisions"]) > 0
        assert len(data["column_profiles"]) > 0

    def test_save_mappings_replaces_previous(self, client: TestClient, auth_headers):
        upload_id = self._upload(client, auth_headers)
        first = [
            {"source_column_name": "name", "target_field_name": "full_name", "confirmed": True, "overridden_by_user": False},
        ]
        client.post(
            f"/api/v3/ingestion/uploads/{upload_id}/mapping",
            json=first,
            headers=auth_headers,
        )

        second = [
            {"source_column_name": "name", "target_field_name": "employee_name", "confirmed": True, "overridden_by_user": True},
        ]
        client.post(
            f"/api/v3/ingestion/uploads/{upload_id}/mapping",
            json=second,
            headers=auth_headers,
        )

        get_resp = client.get(
            f"/api/v3/ingestion/uploads/{upload_id}/mapping",
            headers=auth_headers,
        )
        data = get_resp.json()
        assert len(data["decisions"]) == 1
        assert data["decisions"][0]["target_field_name"] == "employee_name"

    def test_mappings_not_found(self, client: TestClient, auth_headers):
        resp = client.get(
            "/api/v3/ingestion/uploads/nonexistent/mapping",
            headers=auth_headers,
        )
        assert resp.status_code == 404

        save_resp = client.post(
            "/api/v3/ingestion/uploads/nonexistent/mapping",
            json=[],
            headers=auth_headers,
        )
        assert save_resp.status_code == 404
