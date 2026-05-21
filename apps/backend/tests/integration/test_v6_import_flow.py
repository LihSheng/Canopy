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


def test_v6_full_import_flow(client: TestClient, auth_headers, monkeypatch, tmp_path):
    from common.config import settings

    monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)

    project_resp = client.post(
        "/api/projects/",
        json={"name": "V6 Import Project", "description": "Test project"},
        headers=auth_headers,
    )
    assert project_resp.status_code == 201
    project_id = project_resp.json()["id"]

    xlsx_mime = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    preview_resp = client.post(
        "/api/connections/preview",
        files={"file": ("payroll.xlsx", _make_xlsx_bytes(), xlsx_mime)},
        headers=auth_headers,
    )
    assert preview_resp.status_code == 200
    preview = preview_resp.json()
    assert preview["file_name"] == "payroll.xlsx"
    assert preview["sheet_profiles"][0]["sheet_name"] == "Payroll"
    assert preview["sheet_profiles"][0]["row_count"] == 3
    assert preview["sheet_profiles"][0]["data_row_count"] == 2
    assert preview["sheet_profiles"][0]["preview_columns"] == ["name", "amount"]
    assert preview["sheet_profiles"][0]["preview_rows"][0] == ["Alice", 100]

    connection_resp = client.post(
        "/api/connections/",
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
        "/api/datasets/",
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

    get_resp = client.get(f"/api/datasets/{dataset['id']}", headers=auth_headers)
    assert get_resp.status_code == 200
    fetched = get_resp.json()
    assert fetched["active_version_id"] is not None
    assert fetched["id"] == dataset["id"]

    versions_resp = client.get(f"/api/datasets/{dataset['id']}/versions", headers=auth_headers)
    assert versions_resp.status_code == 200
    versions = versions_resp.json()
    assert len(versions) == 1
    assert versions[0]["status"] == "ready"
    assert versions[0]["row_count"] == 2
    assert isinstance(versions[0].get("cleaning_issues"), list)

    preview_dataset_resp = client.get(
        f"/api/datasets/{dataset['id']}/preview", headers=auth_headers
    )
    assert preview_dataset_resp.status_code == 200
    preview_dataset = preview_dataset_resp.json()
    assert preview_dataset["columns"] == ["name", "amount"]
    assert preview_dataset["rows"][0] == ["Alice", 100]
    assert preview_dataset["total_row_count"] == 2

    lineage_resp = client.get(f"/api/datasets/{dataset['id']}/lineage", headers=auth_headers)
    assert lineage_resp.status_code == 200
    lineage = lineage_resp.json()
    assert "nodes" in lineage
    assert "edges" in lineage
    assert len(lineage["nodes"]) >= 3
    node_types = {n["type"] for n in lineage["nodes"]}
    assert "source_object" in node_types
    assert "connection" in node_types
    assert "dataset" in node_types
    assert "version" in node_types
    edge_types = {e["type"] for e in lineage["edges"]}
    assert "feeds" in edge_types or "provides" in edge_types or "belongs_to" in edge_types

    health_resp = client.get(f"/api/datasets/{dataset['id']}/health", headers=auth_headers)
    assert health_resp.status_code == 200
    health = health_resp.json()
    assert health["dataset_id"] == dataset["id"]
    assert health["row_count"] == 2
    assert health["column_count"] == 2

    dataset2_resp = client.post(
        "/api/datasets/",
        json={
            "project_id": project_id,
            "connection_id": connection_id,
            "name": "Payroll v2",
            "source_object_name": "Payroll",
        },
        headers=auth_headers,
    )
    assert dataset2_resp.status_code == 201
    dataset2 = dataset2_resp.json()
    assert dataset2["active_version_id"] is not None

    versions2_resp = client.get(f"/api/datasets/{dataset2['id']}/versions", headers=auth_headers)
    assert versions2_resp.status_code == 200
    versions2 = versions2_resp.json()
    assert len(versions2) == 1

    preview2_resp = client.get(f"/api/datasets/{dataset2['id']}/preview", headers=auth_headers)
    assert preview2_resp.status_code == 200
    preview2 = preview2_resp.json()
    assert preview2["total_row_count"] == 2


def test_source_types_static_file_enabled_mysql_disabled(client: TestClient, auth_headers):
    resp = client.get("/api/source-types/", headers=auth_headers)
    assert resp.status_code == 200
    source_types = resp.json()

    static_file = next((st for st in source_types if st["key"] == "static_file"), None)
    assert static_file is not None
    assert static_file["enabled"] is True

    mysql = next((st for st in source_types if st["key"] == "mysql"), None)
    assert mysql is not None
    assert mysql["enabled"] is True
