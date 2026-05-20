import pytest
from fastapi.testclient import TestClient
from dataset.domain import DatasetVersionStatus
import io
import openpyxl

# Use the same setup as other integration tests
# Assuming fixtures like client, auth_headers, monkeypatch, tmp_path are available via conftest.py

def _make_xlsx_bytes(data: list[list]) -> io.BytesIO:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Payroll"  # Added this line
    for row in data:
        sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer

def _create_dataset_via_api(client, auth_headers, monkeypatch, tmp_path, xlsx_buffer, project_name, connection_name, dataset_name):
    # (Copied helper from test_data_source_api.py)
    from common.config import settings
    monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)
    project_resp = client.post("/api/projects/", json={"name": project_name, "description": "Test project"}, headers=auth_headers)
    project_id = project_resp.json()["id"]
    preview_resp = client.post("/api/connections/preview", files={"file": ("data.xlsx", xlsx_buffer, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}, headers=auth_headers)
    preview = preview_resp.json()
    connection_resp = client.post("/api/connections/", json={"project_id": project_id, "source_type": "static_file", "name": connection_name, "config_json": {"file_name": preview["file_name"], "source_file_path": preview["source_file_path"]}}, headers=auth_headers)
    connection_id = connection_resp.json()["id"]
    dataset_resp = client.post("/api/datasets/", json={"project_id": project_id, "connection_id": connection_id, "name": dataset_name, "source_object_name": "Payroll"}, headers=auth_headers)
    return dataset_resp.json()["id"]

def test_reimport_dataset_version_api(client: TestClient, auth_headers, monkeypatch, tmp_path):
    dataset_id = _create_dataset_via_api(
        client, auth_headers, monkeypatch, tmp_path,
        _make_xlsx_bytes([["name", "amount"], ["Alice", 100]]),
        "Reimport Project", "Reimport Conn", "Reimport Dataset",
    )

    csv_path = tmp_path / "new.csv"
    csv_path.write_text("name,amount\nAlice,100\n", encoding="utf-8")
    
    # Act: Reimport
    resp = client.post(
        f"/api/datasets/{dataset_id}/reimport",
        json={"data_path": str(csv_path), "columns": ["name", "amount", "new_col"]},
        headers=auth_headers,
    )
    
    # Assert
    assert resp.status_code == 201
    data = resp.json()
    assert data["version_number"] == 2
    assert data["status"] == DatasetVersionStatus.READY.value
    
    dataset_resp = client.get(f"/api/datasets/{dataset_id}", headers=auth_headers)
    assert dataset_resp.json()["active_version_id"] == data["id"]

    preview_resp = client.get(
        f"/api/datasets/{dataset_id}/preview?page=1&page_size=100",
        headers=auth_headers,
    )
    assert preview_resp.status_code == 200
    preview = preview_resp.json()
    assert preview["columns"] == ["name", "amount"]
    assert preview["rows"] == [["Alice", "100"]]
