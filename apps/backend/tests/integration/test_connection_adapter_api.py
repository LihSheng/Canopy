"""Integration tests for database connection test and table discovery endpoints."""

from base64 import b64decode
from unittest.mock import AsyncMock, patch

import pytest

from connection.secret_store import ENCRYPTED_VALUE_PREFIX

# Patch at the module where get_adapter is defined
_ADAPTER_PATCH = "connection.database_adapter.get_adapter"

# Ensure SecretStore has a key for the test environment
_TEST_SECRET_KEY = "a1b2c3d4e5f6g7h8a1b2c3d4e5f6g7h8"


@pytest.fixture(autouse=True)
def _set_secret_key(monkeypatch):
    monkeypatch.setenv("SECRET_KEY", _TEST_SECRET_KEY)


pytestmark = pytest.mark.api_schema


class TestPasswordEncryptionAtRest:
    """Verify config_json.password is encrypted before storage."""

    def test_create_connection_stores_encrypted_password(self, client, auth_headers):
        plaintext = "my-s3cret-pass"
        conn_resp = client.post(
            "/api/connections/",
            json={
                "project_id": "p-1",
                "source_type": "postgresql",
                "name": "Encrypted PG",
                "config_json": {
                    "host": "localhost",
                    "port": 5432,
                    "database": "enc_test",
                    "username": "app",
                    "password": plaintext,
                },
            },
            headers=auth_headers,
        )
        assert conn_resp.status_code == 201
        conn_id = conn_resp.json()["id"]

        # GET the connection — the password in the API response should be encrypted
        get_resp = client.get(f"/api/connections/{conn_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        stored_password = data["config_json"].get("password")

        # Password must exist and not be the original plaintext
        assert stored_password is not None
        assert stored_password != plaintext
        assert stored_password.startswith(ENCRYPTED_VALUE_PREFIX)

        # It should look like base64 (valid encrypted blob)
        try:
            raw = b64decode(stored_password.removeprefix(ENCRYPTED_VALUE_PREFIX))
            # AES-GCM: 12-byte nonce + at least 16 bytes ciphertext+tag
            assert len(raw) >= 28
        except Exception:
            pytest.fail("Stored password is not valid base64 — encryption may not have run")

        # Non-secret fields are readable
        assert data["config_json"]["host"] == "localhost"
        assert data["config_json"]["port"] == 5432
        assert data["config_json"]["database"] == "enc_test"
        assert data["config_json"]["username"] == "app"

    def test_connection_without_password_is_stored_as_is(self, client, auth_headers):
        conn_resp = client.post(
            "/api/connections/",
            json={
                "project_id": "p-1",
                "source_type": "postgresql",
                "name": "NoPassword PG",
                "config_json": {"host": "localhost", "port": 5432, "database": "noauth"},
            },
            headers=auth_headers,
        )
        assert conn_resp.status_code == 201
        conn_id = conn_resp.json()["id"]

        get_resp = client.get(f"/api/connections/{conn_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.json()

        assert "password" not in data["config_json"]
        assert data["config_json"]["database"] == "noauth"


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
            mock_adapter.test_connection = AsyncMock(
                return_value={
                    "success": True,
                    "supports_cdc": True,
                    "cdc_parameters": {
                        "replication_slot_name": "canopy_slot_testdb",
                        "wal_level": "logical",
                    },
                }
            )

            resp = client.post(f"/api/connections/{conn_id}/test", headers=auth_headers)

        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert resp.json()["supports_cdc"] is True

        get_resp = client.get(f"/api/connections/{conn_id}", headers=auth_headers)
        assert get_resp.status_code == 200
        data = get_resp.json()
        assert data["config_json"]["supports_cdc"] is True
        assert data["config_json"]["cdc_parameters"]["wal_level"] == "logical"

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
            mock_adapter.test_connection = AsyncMock(return_value={"success": False, "message": "Connection refused"})

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
