from __future__ import annotations

import io

import openpyxl
import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.api_schema


def _make_xlsx_bytes() -> io.BytesIO:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Payroll"
    sheet.append(["name", "amount"])
    sheet.append(["Alice", 100])
    sheet.append(["Bob", 200])
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def test_static_file_preview_and_dataset_creation(client: TestClient, auth_headers, monkeypatch, tmp_path):
    from common.config import settings

    monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)

    project_resp = client.post(
        "/api/v4/projects/",
        json={"name": "Import Project", "description": "Test project"},
        headers=auth_headers,
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    preview_resp = client.post(
        "/api/v4/connections/preview",
        files={"file": ("payroll.xlsx", _make_xlsx_bytes(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert preview_resp.status_code == 200
    preview = preview_resp.json()
    assert preview["file_name"] == "payroll.xlsx"
    assert preview["sheet_profiles"][0]["sheet_name"] == "Payroll"
    assert preview["sheet_profiles"][0]["row_count"] == 3

    connection_resp = client.post(
        "/api/v4/connections/",
        json={
            "project_id": project_id,
            "source_type": "static_file",
            "name": "Payroll file",
            "config_json": {
                "file_name": preview["file_name"],
                "source_file_path": preview["source_file_path"],
            },
        },
        headers=auth_headers,
    )
    assert connection_resp.status_code == 201
    connection_id = connection_resp.json()["id"]

    dataset_resp = client.post(
        "/api/v4/datasets/",
        json={
            "project_id": project_id,
            "connection_id": connection_id,
            "name": "Payroll",
            "source_object_name": "Payroll",
        },
        headers=auth_headers,
    )
    assert dataset_resp.status_code == 201
    dataset = dataset_resp.json()
    assert dataset["active_version_id"] is not None

    versions_resp = client.get(f"/api/v4/datasets/{dataset['id']}/versions", headers=auth_headers)
    assert versions_resp.status_code == 200
    versions = versions_resp.json()
    assert len(versions) == 1
    assert versions[0]["status"] == "ready"
    assert versions[0]["row_count"] == 2

    preview_dataset_resp = client.get(f"/api/v4/datasets/{dataset['id']}/preview", headers=auth_headers)
    assert preview_dataset_resp.status_code == 200
    preview_dataset = preview_dataset_resp.json()
    assert preview_dataset["columns"] == ["name", "amount"]
    assert preview_dataset["rows"][0] == ["Alice", 100]
