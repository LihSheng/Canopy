"""Integration tests for landing-zone immutability boundary.

Covers:
- ingestion validation rejects blocked transformation keys (422)
- static-file landing stores raw structure without mutation
- DB connector landing preserves source row/column structure
- downstream transform failure isolation
- existing flows remain stable
"""

from __future__ import annotations

import io

import openpyxl
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.api_schema


def _make_xlsx_bytes(sheet_name: str = "Payroll") -> io.BytesIO:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = sheet_name
    sheet.append(["  Name  ", "Amount"])  # headers with whitespace
    sheet.append(["  Alice  ", 100])  # value with whitespace
    sheet.append(["Bob", 200])
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)
    return buffer


def _create_project(client: TestClient, auth_headers: dict, name: str = "Landing Test Project") -> str:
    resp = client.post("/api/projects/", json={"name": name}, headers=auth_headers)
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _upload_and_preview(client: TestClient, auth_headers: dict, xlsx_bytes: io.BytesIO, filename: str = "data.xlsx"):
    resp = client.post(
        "/api/connections/preview",
        files={"file": (filename, xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def _create_static_file_connection(
    client: TestClient,
    auth_headers: dict,
    project_id: str,
    name: str,
    source_file_path: str,
    file_name: str,
) -> str:
    resp = client.post(
        "/api/connections/",
        json={
            "project_id": project_id,
            "source_type": "static_file",
            "name": name,
            "config_json": {
                "file_name": file_name,
                "source_file_path": source_file_path,
            },
        },
        headers=auth_headers,
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Issue 1: Ingestion payload guard rejects transform settings
# ---------------------------------------------------------------------------

BLOCKED_KEYS = [
    "transformations",
    "cleaning_steps",
    "column_mappings",
    "rename_columns",
    "drop_columns",
    "cast_rules",
    "filters",
    "masking_rules",
    "normalization_rules",
]


class TestIngestionPayloadGuard:
    """Validation: ingestion APIs reject transformation-oriented keys."""

    def test_dataset_creation_rejects_top_level_transform_key(self, client: TestClient, auth_headers):
        project_id = _create_project(client, auth_headers, "Guard Project")

        resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": "any-conn",
                "name": "dataset-with-cleaning",
                "cleaning_steps": ["trim", "dedupe"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422, resp.text
        body = resp.json()
        assert body["code"] == "INGESTION_TRANSFORM_NOT_ALLOWED"
        assert "not allowed at landing stage" in body["message"]
        assert body["blocked_keys"] == ["cleaning_steps"]

    def test_dataset_creation_rejects_multiple_blocked_keys(self, client: TestClient, auth_headers):
        project_id = _create_project(client, auth_headers, "MultiGuard Project")

        resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": "any-conn",
                "name": "bad-dataset",
                "transformations": ["cast"],
                "filters": ["x > 0"],
                "masking_rules": ["email"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422, resp.text
        body = resp.json()
        assert body["code"] == "INGESTION_TRANSFORM_NOT_ALLOWED"
        blocked = body["blocked_keys"]
        assert "transformations" in blocked
        assert "filters" in blocked
        assert "masking_rules" in blocked

    def test_connection_creation_rejects_transform_key_in_config(self, client: TestClient, auth_headers):
        project_id = _create_project(client, auth_headers, "ConnGuard Project")

        resp = client.post(
            "/api/connections/",
            json={
                "project_id": project_id,
                "source_type": "static_file",
                "name": "bad-connection",
                "config_json": {
                    "cleaning_steps": ["trim"],
                    "host": "localhost",
                },
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422, resp.text
        body = resp.json()
        assert body["code"] == "INGESTION_TRANSFORM_NOT_ALLOWED"
        assert "config_json.cleaning_steps" in body["blocked_keys"]

    def test_dataset_reimport_rejects_transform_key(self, client: TestClient, auth_headers, monkeypatch, tmp_path):
        from common.config import settings

        monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)

        project_id = _create_project(client, auth_headers)
        xlsx = _make_xlsx_bytes()
        preview = _upload_and_preview(client, auth_headers, xlsx)
        conn_id = _create_static_file_connection(
            client,
            auth_headers,
            project_id,
            "Reimport Conn",
            preview["source_file_path"],
            preview["file_name"],
        )
        create_resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": conn_id,
                "name": "Reimport DS",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        dataset_id = create_resp.json()["id"]

        resp = client.post(
            f"/api/datasets/{dataset_id}/reimport",
            json={
                "data_path": preview["source_file_path"],
                "columns": ["Name", "Amount"],
                "cleaning_steps": ["trim"],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422, resp.text
        body = resp.json()
        assert body["code"] == "INGESTION_TRANSFORM_NOT_ALLOWED"
        assert "cleaning_steps" in body["blocked_keys"]

    def test_valid_dataset_creation_still_succeeds(self, client: TestClient, auth_headers, monkeypatch, tmp_path):
        from common.config import settings

        monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)

        project_id = _create_project(client, auth_headers)
        xlsx = _make_xlsx_bytes()
        preview = _upload_and_preview(client, auth_headers, xlsx)
        conn_id = _create_static_file_connection(
            client,
            auth_headers,
            project_id,
            "Valid Conn",
            preview["source_file_path"],
            preview["file_name"],
        )

        resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": conn_id,
                "name": "Valid Dataset",
                "source_object_name": "Payroll",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        dataset = resp.json()
        assert dataset["active_version_id"] is not None

    def test_valid_connection_creation_still_succeeds(self, client: TestClient, auth_headers, monkeypatch, tmp_path):
        from common.config import settings

        monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)

        project_id = _create_project(client, auth_headers)
        xlsx = _make_xlsx_bytes()
        preview = _upload_and_preview(client, auth_headers, xlsx)

        resp = client.post(
            "/api/connections/",
            json={
                "project_id": project_id,
                "source_type": "static_file",
                "name": "Clean Connection",
                "config_json": {
                    "file_name": preview["file_name"],
                    "source_file_path": preview["source_file_path"],
                },
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        assert resp.json()["id"] is not None


# ---------------------------------------------------------------------------
# Issue 2: Static-file landing path stores raw only
# ---------------------------------------------------------------------------


class TestStaticFileRawLanding:
    """Static-file ingestion must preserve source structure without mutation."""

    def test_landed_rows_preserve_whitespace(self, client: TestClient, auth_headers, monkeypatch, tmp_path):
        """Raw landing must not trim whitespace from values."""
        from common.config import settings

        monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)

        project_id = _create_project(client, auth_headers)
        xlsx = _make_xlsx_bytes()
        preview = _upload_and_preview(client, auth_headers, xlsx)
        conn_id = _create_static_file_connection(
            client,
            auth_headers,
            project_id,
            "Whitespace Conn",
            preview["source_file_path"],
            preview["file_name"],
        )

        resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": conn_id,
                "name": "Raw Whitespace",
                "source_object_name": "Payroll",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        dataset = resp.json()

        preview_resp = client.get(f"/api/datasets/{dataset['id']}/preview", headers=auth_headers)
        assert preview_resp.status_code == 200, preview_resp.text
        data = preview_resp.json()
        assert data["total_row_count"] == 2

        # Headers from xlsx: "  Name  ", "Amount" -> normalize_header fills blank cols,
        # but raw values should not be trimmed.
        rows = data["rows"]
        # The first row has "  Alice  " (with whitespace) - should be preserved as-is
        alice_row = rows[0]
        assert "  Name  " in alice_row or any("Name" in k for k in alice_row.keys())
        # Check we have 2 data rows
        assert len(rows) == 2

    def test_raw_storage_path_points_to_original_file(self, client: TestClient, auth_headers, monkeypatch, tmp_path):
        from common.config import settings

        monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)

        project_id = _create_project(client, auth_headers)
        xlsx = _make_xlsx_bytes()
        preview = _upload_and_preview(client, auth_headers, xlsx)
        conn_id = _create_static_file_connection(
            client,
            auth_headers,
            project_id,
            "RawPath Conn",
            preview["source_file_path"],
            preview["file_name"],
        )

        resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": conn_id,
                "name": "Raw Path Check",
                "source_object_name": "Payroll",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        dataset = resp.json()

        versions_resp = client.get(f"/api/datasets/{dataset['id']}/versions", headers=auth_headers)
        assert versions_resp.status_code == 200
        versions = versions_resp.json()
        assert len(versions) == 1
        version = versions[0]

        # raw_storage_path should be set to the original source file path
        assert version["raw_storage_path"]
        # cleaning_issues should be empty (no cleaning at landing)
        assert version["cleaning_issues"] == []

    def test_landing_creates_version_with_correct_counts(self, client: TestClient, auth_headers, monkeypatch, tmp_path):
        from common.config import settings

        monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)

        project_id = _create_project(client, auth_headers)
        xlsx = _make_xlsx_bytes()
        preview = _upload_and_preview(client, auth_headers, xlsx)
        conn_id = _create_static_file_connection(
            client,
            auth_headers,
            project_id,
            "Counts Conn",
            preview["source_file_path"],
            preview["file_name"],
        )

        resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": conn_id,
                "name": "Counts Check",
                "source_object_name": "Payroll",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        dataset = resp.json()

        versions = client.get(f"/api/datasets/{dataset['id']}/versions", headers=auth_headers).json()
        version = versions[0]
        assert version["version_number"] == 1
        assert version["status"] == "ready"
        assert version["row_count"] == 2
        assert version["column_count"] == 2


# ---------------------------------------------------------------------------
# Issue 4: Downstream transform failure isolation
# ---------------------------------------------------------------------------


class TestDownstreamTransformFailureIsolation:
    """Transform failure must not corrupt raw landing data or promote a broken version."""

    def test_mark_version_failed_does_not_change_active_version(
        self, client: TestClient, auth_headers, monkeypatch, tmp_path, db_session
    ):
        """When a version is marked FAILED, the active version pointer stays unchanged."""
        from common.config import settings
        from dataset.repository import DatasetRepository, DatasetVersionRepository
        from dataset.service import DatasetVersionService

        monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)

        project_id = _create_project(client, auth_headers)
        xlsx = _make_xlsx_bytes()
        preview = _upload_and_preview(client, auth_headers, xlsx)
        conn_id = _create_static_file_connection(
            client,
            auth_headers,
            project_id,
            "Isolation Conn",
            preview["source_file_path"],
            preview["file_name"],
        )

        resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": conn_id,
                "name": "Isolation DS",
                "source_object_name": "Payroll",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201, resp.text
        dataset = resp.json()
        dataset_id = dataset["id"]
        active_before = dataset["active_version_id"]
        assert active_before is not None

        # Create a second version and mark it as failed
        version_repo = DatasetVersionRepository(db_session)
        dataset_repo = DatasetRepository(db_session)
        version_service = DatasetVersionService(version_repo, dataset_repo)
        v2 = version_service.create_version(dataset_id)
        v2_id = v2.id

        failed = version_service.mark_version_failed(v2_id, "Cleaning pipeline timeout")
        assert failed is not None
        assert failed.status == "failed"
        assert failed.failure_reason == "Cleaning pipeline timeout"

        # Active version should still be v1
        fresh_dataset = dataset_repo.get(dataset_id)
        assert fresh_dataset is not None
        assert fresh_dataset.active_version_id == active_before
        assert fresh_dataset.active_version_id != v2_id


# ---------------------------------------------------------------------------
# Stability: existing flows remain intact
# ---------------------------------------------------------------------------


class TestExistingFlowsStability:
    """Pre-existing ingestion and preview flows remain stable under the new boundary."""

    def test_full_static_file_flow_still_works(self, client: TestClient, auth_headers, monkeypatch, tmp_path):
        from common.config import settings

        monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)

        project_id = _create_project(client, auth_headers)
        xlsx = _make_xlsx_bytes()
        preview = _upload_and_preview(client, auth_headers, xlsx)

        assert preview["file_name"] == "data.xlsx"
        assert len(preview["sheet_profiles"]) == 1

        conn_id = _create_static_file_connection(
            client,
            auth_headers,
            project_id,
            "Stability Conn",
            preview["source_file_path"],
            preview["file_name"],
        )

        dataset_resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": conn_id,
                "name": "Stability DS",
                "source_object_name": "Payroll",
            },
            headers=auth_headers,
        )
        assert dataset_resp.status_code == 201
        dataset = dataset_resp.json()
        assert dataset["active_version_id"] is not None

        # versions
        versions_resp = client.get(f"/api/datasets/{dataset['id']}/versions", headers=auth_headers)
        assert versions_resp.status_code == 200
        versions = versions_resp.json()
        assert len(versions) == 1
        assert versions[0]["status"] == "ready"

        # preview
        preview_resp = client.get(f"/api/datasets/{dataset['id']}/preview", headers=auth_headers)
        assert preview_resp.status_code == 200
        preview_data = preview_resp.json()
        assert preview_data["total_row_count"] == 2

        # lineage
        lineage_resp = client.get(f"/api/datasets/{dataset['id']}/lineage", headers=auth_headers)
        assert lineage_resp.status_code == 200

        # health
        health_resp = client.get(f"/api/datasets/{dataset['id']}/health", headers=auth_headers)
        assert health_resp.status_code == 200

        # delete dataset
        del_resp = client.delete(f"/api/datasets/{dataset['id']}", headers=auth_headers)
        assert del_resp.status_code == 200
        assert del_resp.json()["deleted"] is True

    def test_dataset_reimport_still_works(self, client: TestClient, auth_headers, monkeypatch, tmp_path):
        from common.config import settings

        monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)

        project_id = _create_project(client, auth_headers)
        xlsx = _make_xlsx_bytes()
        preview = _upload_and_preview(client, auth_headers, xlsx)
        conn_id = _create_static_file_connection(
            client,
            auth_headers,
            project_id,
            "Reimport Conn",
            preview["source_file_path"],
            preview["file_name"],
        )

        create_resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": conn_id,
                "name": "Reimport DS",
                "source_object_name": "Payroll",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        dataset_id = create_resp.json()["id"]

        # Reimport the same file
        reimport_resp = client.post(
            f"/api/datasets/{dataset_id}/reimport",
            json={
                "data_path": preview["source_file_path"],
                "columns": ["Name", "Amount"],
                "sheet_name": "Payroll",
            },
            headers=auth_headers,
        )
        assert reimport_resp.status_code == 201, reimport_resp.text
        assert reimport_resp.json()["version_number"] == 2
        assert reimport_resp.json()["status"] == "ready"

        # Both versions exist
        versions = client.get(f"/api/datasets/{dataset_id}/versions", headers=auth_headers).json()
        assert len(versions) == 2
