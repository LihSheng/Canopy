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


class TestCleaningTemplates:
    def _upload(self, client: TestClient, auth_headers) -> str:
        resp = client.post(
            "/api/v3/ingestion/uploads",
            files={"file": ("data.csv", io.BytesIO(b"name,amount\nAlice,100"), "text/csv")},
            data={"source_profile": "herdhr", "dataset_type": "payroll"},
            headers=auth_headers,
        )
        return resp.json()["upload_id"]

    def test_create_pipeline(self, client: TestClient, auth_headers):
        upload_id = self._upload(client, auth_headers)
        resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "draft"
        assert data["upload_id"] == upload_id
        assert len(data["steps"]) == 0

    def test_create_pipeline_duplicate_fails(self, client: TestClient, auth_headers):
        upload_id = self._upload(client, auth_headers)
        client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "already exists" in resp.text

    def test_get_pipeline(self, client: TestClient, auth_headers):
        upload_id = self._upload(client, auth_headers)
        create_resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        pipeline_id = create_resp.json()["id"]

        resp = client.get(f"/api/v3/ingestion/templates/{pipeline_id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == pipeline_id
        assert data["upload_id"] == upload_id

    def test_get_pipeline_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/v3/ingestion/templates/nonexistent", headers=auth_headers)
        assert resp.status_code == 404

    def test_replace_steps(self, client: TestClient, auth_headers):
        upload_id = self._upload(client, auth_headers)
        create_resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        pipeline_id = create_resp.json()["id"]

        steps = [
            {"step_type": "trim", "order": 0, "parameters": {"columns": ["name"]}, "description": None},
            {"step_type": "rename", "order": 1, "parameters": {"mappings": {"name": "employee_name"}}, "description": None},
        ]
        resp = client.put(
            f"/api/v3/ingestion/templates/{pipeline_id}/steps",
            json=steps,
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["step_type"] == "trim"
        assert data[1]["step_type"] == "rename"

    def test_reorder_steps(self, client: TestClient, auth_headers):
        upload_id = self._upload(client, auth_headers)
        create_resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        pipeline_id = create_resp.json()["id"]

        steps_resp = client.put(
            f"/api/v3/ingestion/templates/{pipeline_id}/steps",
            json=[
                {"step_type": "trim", "order": 0, "parameters": {"columns": ["name"]}, "description": None},
                {"step_type": "cast", "order": 1, "parameters": {"columns": {"amount": "number"}}, "description": None},
            ],
            headers=auth_headers,
        )
        step_ids = [s["id"] for s in steps_resp.json()]

        reordered = client.patch(
            f"/api/v3/ingestion/templates/{pipeline_id}/steps/reorder",
            json={"step_ids": [step_ids[1], step_ids[0]]},
            headers=auth_headers,
        )
        assert reordered.status_code == 200
        data = reordered.json()
        assert data[0]["step_type"] == "cast"
        assert data[1]["step_type"] == "trim"

    def test_publish_pipeline(self, client: TestClient, auth_headers):
        upload_id = self._upload(client, auth_headers)
        create_resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        pipeline_id = create_resp.json()["id"]

        client.put(
            f"/api/v3/ingestion/templates/{pipeline_id}/steps",
            json=[
                {"step_type": "trim", "order": 0, "parameters": {"columns": ["name"]}, "description": None},
            ],
            headers=auth_headers,
        )

        resp = client.patch(
            f"/api/v3/ingestion/templates/{pipeline_id}/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "published"

    def test_publish_empty_pipeline_fails(self, client: TestClient, auth_headers):
        upload_id = self._upload(client, auth_headers)
        create_resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        pipeline_id = create_resp.json()["id"]

        resp = client.patch(
            f"/api/v3/ingestion/templates/{pipeline_id}/publish",
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_modify_published_pipeline_fails(self, client: TestClient, auth_headers):
        upload_id = self._upload(client, auth_headers)
        create_resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        pipeline_id = create_resp.json()["id"]

        client.put(
            f"/api/v3/ingestion/templates/{pipeline_id}/steps",
            json=[
                {"step_type": "trim", "order": 0, "parameters": {"columns": ["name"]}, "description": None},
            ],
            headers=auth_headers,
        )
        client.patch(
            f"/api/v3/ingestion/templates/{pipeline_id}/publish",
            headers=auth_headers,
        )

        resp = client.put(
            f"/api/v3/ingestion/templates/{pipeline_id}/steps",
            json=[{"step_type": "cast", "order": 0, "parameters": {"columns": {"amount": "number"}}, "description": None}],
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "published" in resp.text.lower()

    def test_validate_pipeline_endpoint(self, client: TestClient, auth_headers):
        upload_id = self._upload(client, auth_headers)
        create_resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        pipeline_id = create_resp.json()["id"]

        client.put(
            f"/api/v3/ingestion/templates/{pipeline_id}/steps",
            json=[
                {"step_type": "trim", "order": 0, "parameters": {"columns": ["name"]}, "description": None},
            ],
            headers=auth_headers,
        )

        resp = client.post(
            f"/api/v3/ingestion/templates/{pipeline_id}/validate",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "warnings" in data

    def test_create_pipeline_unauthorized(self, client: TestClient):
        resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": "test"},
        )
        assert resp.status_code == 401


class TestProcessEndpoint:
    def _setup_full(self, client: TestClient, auth_headers) -> tuple[str, str]:
        buf = _make_xlsx([["name", "amount", "date"], ["Alice", 100, "2024-01-15"], ["Bob", 200, "2024-02-20"]])
        resp = client.post(
            "/api/v3/ingestion/uploads",
            files={"file": ("data.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"source_profile": "herdhr", "dataset_type": "payroll"},
            headers=auth_headers,
        )
        upload_id = resp.json()["upload_id"]

        pipe_resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        pipeline_id = pipe_resp.json()["id"]

        client.put(
            f"/api/v3/ingestion/templates/{pipeline_id}/steps",
            json=[
                {"step_type": "trim", "order": 0, "parameters": {"columns": ["name"]}, "description": None},
            ],
            headers=auth_headers,
        )

        fam_resp = client.post(
            "/api/v3/ingestion/template-families",
            json={"dataset_type": "payroll", "source_profile": "herdhr", "name": "Test Family", "description": ""},
            headers=auth_headers,
        )
        template_id = fam_resp.json()["id"]

        ver_resp = client.post(
            f"/api/v3/ingestion/template-families/{template_id}/versions",
            json={"spec_json": {"steps": [
                {"step_type": "trim", "order": 0, "parameters": {"columns": ["name"]}},
            ]}},
            headers=auth_headers,
        )
        version_id = ver_resp.json()["id"]

        client.post(
            f"/api/v3/ingestion/template-families/{template_id}/versions/{version_id}/publish",
            headers=auth_headers,
        )

        client.put(
            f"/api/v3/ingestion/templates/{pipeline_id}/bind",
            json={"template_version_id": version_id},
            headers=auth_headers,
        )

        return upload_id, pipeline_id

    def test_process_endpoint_success(self, client: TestClient, auth_headers):
        upload_id, _ = self._setup_full(client, auth_headers)
        resp = client.post(f"/api/v3/ingestion/uploads/{upload_id}/process", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "cleaned_snapshot_id" in data
        assert data["status"] in ("completed", "completed_with_warnings")
        assert data["row_count"] > 0

    def test_process_no_template_bound_fails(self, client: TestClient, auth_headers):
        buf = _make_xlsx([["name"], ["Alice"]])
        resp = client.post(
            "/api/v3/ingestion/uploads",
            files={"file": ("data.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"source_profile": "herdhr", "dataset_type": "payroll"},
            headers=auth_headers,
        )
        upload_id = resp.json()["upload_id"]

        resp = client.post(f"/api/v3/ingestion/uploads/{upload_id}/process", headers=auth_headers)
        assert resp.status_code == 400

    def test_process_returns_correct_stats(self, client: TestClient, auth_headers):
        upload_id, _ = self._setup_full(client, auth_headers)
        resp = client.post(f"/api/v3/ingestion/uploads/{upload_id}/process", headers=auth_headers)
        data = resp.json()
        assert data["row_count"] == 2
        assert isinstance(data["warning_count"], int)
        assert isinstance(data["warnings"], list)

    def test_get_cleaned_snapshot(self, client: TestClient, auth_headers):
        upload_id, _ = self._setup_full(client, auth_headers)
        client.post(f"/api/v3/ingestion/uploads/{upload_id}/process", headers=auth_headers)
        resp = client.get(f"/api/v3/ingestion/uploads/{upload_id}/cleaned", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["upload_id"] == upload_id
        assert data["row_count"] > 0

    def test_get_cleaned_snapshot_not_found(self, client: TestClient, auth_headers):
        resp = client.get("/api/v3/ingestion/uploads/nonexistent/cleaned", headers=auth_headers)
        assert resp.status_code == 404

    def test_process_unauthorized(self, client: TestClient):
        resp = client.post("/api/v3/ingestion/uploads/nonexistent/process")
        assert resp.status_code == 401


class TestLineageEndpoint:
    def _setup_processed(self, client: TestClient, auth_headers) -> str:
        buf = _make_xlsx([["name", "amount"], ["Alice", 100], ["Bob", 200]])
        resp = client.post(
            "/api/v3/ingestion/uploads",
            files={"file": ("data.xlsx", buf, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            data={"source_profile": "herdhr", "dataset_type": "payroll"},
            headers=auth_headers,
        )
        upload_id = resp.json()["upload_id"]

        pipe_resp = client.post(
            "/api/v3/ingestion/templates",
            json={"upload_id": upload_id},
            headers=auth_headers,
        )
        pipeline_id = pipe_resp.json()["id"]

        client.put(
            f"/api/v3/ingestion/templates/{pipeline_id}/steps",
            json=[
                {"step_type": "trim", "order": 0, "parameters": {"columns": ["name"]}, "description": None},
            ],
            headers=auth_headers,
        )

        fam_resp = client.post(
            "/api/v3/ingestion/template-families",
            json={"dataset_type": "payroll", "source_profile": "herdhr", "name": "Test Family", "description": ""},
            headers=auth_headers,
        )
        template_id = fam_resp.json()["id"]

        ver_resp = client.post(
            f"/api/v3/ingestion/template-families/{template_id}/versions",
            json={"spec_json": {"steps": [
                {"step_type": "trim", "order": 0, "parameters": {"columns": ["name"]}},
            ]}},
            headers=auth_headers,
        )
        version_id = ver_resp.json()["id"]

        client.post(
            f"/api/v3/ingestion/template-families/{template_id}/versions/{version_id}/publish",
            headers=auth_headers,
        )

        client.put(
            f"/api/v3/ingestion/templates/{pipeline_id}/bind",
            json={"template_version_id": version_id},
            headers=auth_headers,
        )

        client.post(f"/api/v3/ingestion/uploads/{upload_id}/process", headers=auth_headers)
        return upload_id

    def test_lineage_returns_graph_after_processing(self, client: TestClient, auth_headers):
        upload_id = self._setup_processed(client, auth_headers)
        resp = client.get(f"/api/v3/ingestion/uploads/{upload_id}/lineage", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["upload_id"] == upload_id
        assert len(data["nodes"]) > 0
        assert len(data["edges"]) > 0

    def test_lineage_has_correct_node_types(self, client: TestClient, auth_headers):
        upload_id = self._setup_processed(client, auth_headers)
        resp = client.get(f"/api/v3/ingestion/uploads/{upload_id}/lineage", headers=auth_headers)
        data = resp.json()
        node_types = {n["node_type"] for n in data["nodes"]}
        assert "file" in node_types
        assert "sheet" in node_types
        assert "raw_column" in node_types

    def test_lineage_edge_directions(self, client: TestClient, auth_headers):
        upload_id = self._setup_processed(client, auth_headers)
        resp = client.get(f"/api/v3/ingestion/uploads/{upload_id}/lineage", headers=auth_headers)
        data = resp.json()
        for edge in data["edges"]:
            assert edge["from_node_id"] != edge["to_node_id"]
            assert edge["edge_type"] in ("derived_from", "normalized_to")

    def test_lineage_not_found_for_unprocessed(self, client: TestClient, auth_headers):
        resp = client.get("/api/v3/ingestion/uploads/nonexistent/lineage", headers=auth_headers)
        assert resp.status_code == 404

    def test_reprocessing_updates_lineage(self, client: TestClient, auth_headers):
        upload_id = self._setup_processed(client, auth_headers)
        resp1 = client.get(f"/api/v3/ingestion/uploads/{upload_id}/lineage", headers=auth_headers)
        assert resp1.status_code == 200
        first_node_count = len(resp1.json()["nodes"])

        resp2 = client.post(f"/api/v3/ingestion/uploads/{upload_id}/process", headers=auth_headers)
        assert resp2.status_code == 200

        resp3 = client.get(f"/api/v3/ingestion/uploads/{upload_id}/lineage", headers=auth_headers)
        assert resp3.status_code == 200
        second_node_count = len(resp3.json()["nodes"])
        assert second_node_count == first_node_count  # same structure after reprocess
