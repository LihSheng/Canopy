"""Integration tests for the sync policy endpoint."""

import pytest

pytestmark = pytest.mark.api_schema


class TestSyncPolicyEndpoint:
    def test_update_sync_policy(self, client, auth_headers):
        # Create a project
        proj_resp = client.post(
            "/api/projects/", json={"name": "Test", "description": ""}, headers=auth_headers
        )
        assert proj_resp.status_code == 201
        project_id = proj_resp.json()["id"]

        # Create a connection
        conn_resp = client.post(
            "/api/connections/",
            json={"project_id": project_id, "source_type": "postgresql", "name": "PG"},
            headers=auth_headers,
        )
        assert conn_resp.status_code == 201
        conn_id = conn_resp.json()["id"]

        # Create a dataset
        ds_resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": conn_id,
                "name": "users",
                "source_object_name": "users",
            },
            headers=auth_headers,
        )
        assert ds_resp.status_code == 201
        ds_id = ds_resp.json()["id"]

        # Update sync policy
        patch_resp = client.patch(
            f"/api/datasets/{ds_id}/sync-policy",
            json={
                "sync_mode": "batch",
                "batch_strategy": "incremental_cursor",
                "cursor_column": "updated_at",
                "frequency_minutes": 60,
            },
            headers=auth_headers,
        )
        assert patch_resp.status_code == 200
        data = patch_resp.json()
        assert data["sync_mode"] == "batch"
        assert data["batch_strategy"] == "incremental_cursor"
        assert data["cursor_column"] == "updated_at"

        # Verify GET reflects changes
        get_resp = client.get(f"/api/datasets/{ds_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["sync_mode"] == "batch"
        assert data["batch_strategy"] == "incremental_cursor"
        assert data["cursor_column"] == "updated_at"

    def test_cursor_column_change_resets_cursor_value(self, client, auth_headers):
        proj_resp = client.post(
            "/api/projects/", json={"name": "Test2", "description": ""}, headers=auth_headers
        )
        assert proj_resp.status_code == 201
        project_id = proj_resp.json()["id"]

        conn_resp = client.post(
            "/api/connections/",
            json={"project_id": project_id, "source_type": "postgresql", "name": "PG2"},
            headers=auth_headers,
        )
        assert conn_resp.status_code == 201
        conn_id = conn_resp.json()["id"]

        ds_resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": conn_id,
                "name": "orders",
                "source_object_name": "orders",
                "sync_mode": "batch",
                "batch_strategy": "incremental_cursor",
                "cursor_column": "created_at",
                "last_cursor_value": "2026-05-19T10:00:00Z",
            },
            headers=auth_headers,
        )
        assert ds_resp.status_code == 201

        # Change cursor column — should reset last_cursor_value
        patch_resp = client.patch(
            f"/api/datasets/{ds_resp.json()['id']}/sync-policy",
            json={"cursor_column": "updated_at"},
            headers=auth_headers,
        )
        assert patch_resp.status_code == 200
        assert patch_resp.json()["last_cursor_value"] is None

    def test_invalid_sync_mode_returns_400(self, client, auth_headers):
        proj_resp = client.post(
            "/api/projects/", json={"name": "T", "description": ""}, headers=auth_headers
        )
        assert proj_resp.status_code == 201
        project_id = proj_resp.json()["id"]

        conn_resp = client.post(
            "/api/connections/",
            json={"project_id": project_id, "source_type": "postgresql", "name": "PG"},
            headers=auth_headers,
        )
        assert conn_resp.status_code == 201
        conn_id = conn_resp.json()["id"]

        ds_resp = client.post(
            "/api/datasets/",
            json={"project_id": project_id, "connection_id": conn_id, "name": "t"},
            headers=auth_headers,
        )
        assert ds_resp.status_code == 201
        ds_id = ds_resp.json()["id"]

        resp = client.patch(
            f"/api/datasets/{ds_id}/sync-policy",
            json={"sync_mode": "quantum"},
            headers=auth_headers,
        )
        assert resp.status_code == 400

    def test_create_dataset_persists_real_time_strategy(self, client, auth_headers):
        proj_resp = client.post(
            "/api/projects/", json={"name": "CDC", "description": ""}, headers=auth_headers
        )
        assert proj_resp.status_code == 201
        project_id = proj_resp.json()["id"]

        conn_resp = client.post(
            "/api/connections/",
            json={"project_id": project_id, "source_type": "postgresql", "name": "CDC PG"},
            headers=auth_headers,
        )
        assert conn_resp.status_code == 201
        conn_id = conn_resp.json()["id"]

        ds_resp = client.post(
            "/api/datasets/",
            json={
                "project_id": project_id,
                "connection_id": conn_id,
                "name": "events",
                "source_object_name": "events",
                "sync_mode": "real_time",
                "real_time_strategy": "cdc",
            },
            headers=auth_headers,
        )
        assert ds_resp.status_code == 201
        data = ds_resp.json()
        assert data["sync_mode"] == "real_time"
        assert data["real_time_strategy"] == "cdc"

        get_resp = client.get(f"/api/datasets/{data['id']}", headers=auth_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["real_time_strategy"] == "cdc"
