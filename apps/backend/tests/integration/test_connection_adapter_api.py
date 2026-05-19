"""Integration tests for database connection test and table discovery endpoints."""

import os
from unittest.mock import AsyncMock, patch

import pytest

# Patch at the route module where get_adapter is imported
_ADAPTER_PATCH = "api.routes.connection.get_adapter"

# Ensure SecretStore has a key for the test environment
_TEST_SECRET_KEY = "a1b2c3d4e5f6g7h8a1b2c3d4e5f6g7h8"


@pytest.fixture(autouse=True)
def _set_secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", _TEST_SECRET_KEY)

pytestmark = pytest.mark.api_schema


class TestConnectionTestEndpoint:
    def test_test_connection_success(self, client, auth_headers):
        # Create a connection first
        conn_resp = client.post(
            "/api/connections/",
            json={
                "project_id": "p-1",
                "source_type": "postgresql",
                "name": "Test PG",
                "config_json": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "testdb",
                    "username": "user",
                },
            },
            headers=auth_headers,
        )
        assert conn_resp.status_code == 201
        conn_id = conn_resp.json()["id"]

        # Mock the adapter
        with patch(_ADAPTER_PATCH) as mock_get:
            mock_adapter = mock_get.return_value
            mock_adapter.test_connection = AsyncMock(return_value={"success": True})

            resp = client.post(f"/api/connections/{conn_id}/test", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_test_connection_failure(self, client, auth_headers):
        conn_resp = client.post(
            "/api/connections/",
            json={
                "project_id": "p-1",
                "source_type": "postgresql",
                "name": "Bad PG",
                "config_json": {"host": "badhost", "port": 5432},
            },
            headers=auth_headers,
        )
        assert conn_resp.status_code == 201
        conn_id = conn_resp.json()["id"]

        with patch(_ADAPTER_PATCH) as mock_get:
            mock_adapter = mock_get.return_value
            mock_adapter.test_connection = AsyncMock(
                return_value={"success": False, "message": "Connection refused"}
            )

            resp = client.post(f"/api/connections/{conn_id}/test", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json()["success"] is False
        assert resp.json()["message"] == "Connection refused"


class TestDiscoveryEndpoint:
    def test_discover_tables(self, client, auth_headers):
        conn_resp = client.post(
            "/api/connections/",
            json={
                "project_id": "p-1",
                "source_type": "postgresql",
                "name": "Discovery PG",
                "config_json": {"host": "localhost", "port": 5432},
            },
            headers=auth_headers,
        )
        assert conn_resp.status_code == 201
        conn_id = conn_resp.json()["id"]

        mock_tables = [
            {
                "table_name": "users",
                "row_count_estimate": 1000,
                "columns": [
                    {"name": "id", "data_type": "bigint"},
                    {"name": "name", "data_type": "varchar"},
                    {"name": "updated_at", "data_type": "timestamp"},
                ],
            },
        ]

        with patch(_ADAPTER_PATCH) as mock_get:
            mock_adapter = mock_get.return_value
            mock_adapter.discover_tables = AsyncMock(return_value=mock_tables)

            resp = client.get(f"/api/connections/{conn_id}/discover", headers=auth_headers)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["table_name"] == "users"
        assert data[0]["row_count_estimate"] == 1000
        assert len(data[0]["columns"]) == 3
        # Cursor detection should be attached to each table
        assert "detected_cursor_column" in data[0]
        assert data[0]["detected_cursor_column"] == "updated_at"


class TestPreviewEndpoint:
    def test_preview_table(self, client, auth_headers):
        conn_resp = client.post(
            "/api/connections/",
            json={
                "project_id": "p-1",
                "source_type": "postgresql",
                "name": "Preview PG",
                "config_json": {"host": "localhost", "port": 5432},
            },
            headers=auth_headers,
        )
        assert conn_resp.status_code == 201
        conn_id = conn_resp.json()["id"]

        mock_preview = {
            "columns": [
                {"name": "id", "data_type": "bigint"},
                {"name": "name", "data_type": "varchar"},
            ],
            "rows": [[1, "Alice"], [2, "Bob"]],
            "detected_cursor_column": None,
            "cursor_candidates": [],
        }

        with patch(_ADAPTER_PATCH) as mock_get:
            mock_adapter = mock_get.return_value
            mock_adapter.preview_table = AsyncMock(return_value=mock_preview)

            resp = client.get(
                f"/api/connections/{conn_id}/discover/users",
                headers=auth_headers,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["columns"]) == 2
        assert len(data["rows"]) == 2
        assert data["detected_cursor_column"] is None
