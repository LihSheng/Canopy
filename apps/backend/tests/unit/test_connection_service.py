"""Unit tests for ConnectionService encryption/decryption boundary.

These tests verify that config_json.password is encrypted on write
and decrypted on read through the service boundary, while non-secret
fields remain readable.
"""

from unittest.mock import MagicMock

import pytest

from connection.domain import Connection, ConnectionStatus
from connection.secret_store import ENCRYPTED_VALUE_PREFIX, AesGcmSecretStore, EncryptionError
from connection.service import ConnectionService

_TEST_KEY = bytes(range(32))
_TEST_PASSWORD = "s3cret!pass"


def _make_store() -> AesGcmSecretStore:
    return AesGcmSecretStore(key=_TEST_KEY)


def _make_connection(config_json: dict | None = None) -> Connection:
    return Connection(
        id="conn-1",
        tenant_id="tenant-1",
        project_id="proj-1",
        source_type="postgresql",
        name="test-db",
        status=ConnectionStatus.ACTIVE.value,
        config_json=config_json or {},
    )


def _mock_repo(saved_connection: Connection) -> MagicMock:
    repo = MagicMock()
    repo.save.return_value = saved_connection
    repo.get.return_value = saved_connection
    return repo


# ---------------------------------------------------------------------------
# _encrypt_config
# ---------------------------------------------------------------------------


class TestEncryptConfig:
    def test_encrypts_password_field(self):
        store = _make_store()
        service = ConnectionService(repo=MagicMock(), secret_store=store)
        result = service._encrypt_config({"host": "localhost", "password": _TEST_PASSWORD})

        assert result["host"] == "localhost"
        assert result["password"] != _TEST_PASSWORD
        assert result["password"].startswith(ENCRYPTED_VALUE_PREFIX)
        # Round-trip: the encrypted value should decrypt back to the original
        assert store.decrypt(result["password"]) == _TEST_PASSWORD

    def test_no_password_key_is_noop(self):
        store = _make_store()
        service = ConnectionService(repo=MagicMock(), secret_store=store)
        result = service._encrypt_config({"host": "localhost", "port": 5432})

        assert result == {"host": "localhost", "port": 5432}

    def test_empty_password_is_noop(self):
        store = _make_store()
        service = ConnectionService(repo=MagicMock(), secret_store=store)
        result = service._encrypt_config({"password": ""})

        assert result == {"password": ""}

    def test_non_string_password_is_noop(self):
        store = _make_store()
        service = ConnectionService(repo=MagicMock(), secret_store=store)
        result = service._encrypt_config({"password": 12345})

        assert result == {"password": 12345}

    def test_leaves_other_config_fields_unchanged(self):
        store = _make_store()
        service = ConnectionService(repo=MagicMock(), secret_store=store)
        config = {
            "host": "db.example.com",
            "port": 5432,
            "database": "analytics",
            "username": "app_user",
            "password": _TEST_PASSWORD,
            "ssl": True,
        }
        result = service._encrypt_config(config)

        assert result["host"] == "db.example.com"
        assert result["port"] == 5432
        assert result["database"] == "analytics"
        assert result["username"] == "app_user"
        assert result["ssl"] is True
        assert result["password"] != _TEST_PASSWORD  # encrypted


# ---------------------------------------------------------------------------
# _decrypt_config
# ---------------------------------------------------------------------------


class TestDecryptConfig:
    def test_decrypts_encrypted_password(self):
        store = _make_store()
        service = ConnectionService(repo=MagicMock(), secret_store=store)
        encrypted_password = store.encrypt(_TEST_PASSWORD)
        conn = _make_connection({"host": "localhost", "password": encrypted_password})

        config = service._decrypt_config(conn)

        assert config["host"] == "localhost"
        assert config["password"] == _TEST_PASSWORD

    def test_no_password_key_is_noop(self):
        store = _make_store()
        service = ConnectionService(repo=MagicMock(), secret_store=store)
        conn = _make_connection({"host": "localhost"})

        config = service._decrypt_config(conn)

        assert config == {"host": "localhost"}

    def test_empty_password_is_noop(self):
        store = _make_store()
        service = ConnectionService(repo=MagicMock(), secret_store=store)
        conn = _make_connection({"password": ""})

        config = service._decrypt_config(conn)

        assert config == {"password": ""}

    def test_legacy_plaintext_pass_through(self):
        """Legacy plaintext passwords should pass through unchanged."""
        store = _make_store()
        service = ConnectionService(repo=MagicMock(), secret_store=store)
        conn = _make_connection({"host": "old-db", "password": "plaintext-legacy"})

        config = service._decrypt_config(conn)

        # Should NOT raise and should return the original plaintext unchanged
        assert config["password"] == "plaintext-legacy"
        assert config["host"] == "old-db"

    def test_wrong_key_on_valid_ciphertext_raises(self):
        """When the ciphertext is valid but the key is wrong, it should raise."""
        store = _make_store()
        encrypted = store.encrypt("secret")
        wrong_store = AesGcmSecretStore(key=bytes(range(32, 64)))
        service = ConnectionService(repo=MagicMock(), secret_store=wrong_store)
        with pytest.raises(EncryptionError, match="Decryption failed"):
            service._decrypt_config(_make_connection({"password": encrypted}))

    def test_non_string_password_is_noop(self):
        store = _make_store()
        service = ConnectionService(repo=MagicMock(), secret_store=store)
        conn = _make_connection({"password": None})

        config = service._decrypt_config(conn)

        assert config["password"] is None


# ---------------------------------------------------------------------------
# create_connection — end-to-end encrypt-on-write
# ---------------------------------------------------------------------------


class TestCreateConnectionEncrypts:
    def test_repo_receives_encrypted_password(self):
        store = _make_store()
        config_in = {"host": "pg.example.com", "password": _TEST_PASSWORD, "port": 5432}

        # Capture what the repo saves
        saved: list[Connection] = []

        repo = MagicMock()
        repo.save.side_effect = lambda c: saved.append(c) or c

        service = ConnectionService(repo=repo, secret_store=store)
        service.create_connection("tenant-1", "proj-1", "postgresql", "test-db", config_in)

        assert len(saved) == 1
        persisted_config = saved[0].config_json

        # Non-secret fields are readable
        assert persisted_config["host"] == "pg.example.com"
        assert persisted_config["port"] == 5432

        # Password is NOT plaintext in the persisted config
        assert persisted_config["password"] != _TEST_PASSWORD

        # Password CAN be decrypted back to the original
        assert store.decrypt(persisted_config["password"]) == _TEST_PASSWORD

    def test_connection_without_password_is_unchanged(self):
        store = _make_store()
        config_in = {"host": "no-auth-db.example.com", "port": 5432}

        saved: list[Connection] = []
        repo = MagicMock()
        repo.save.side_effect = lambda c: saved.append(c) or c

        service = ConnectionService(repo=repo, secret_store=store)
        service.create_connection("tenant-1", "proj-1", "postgresql", "noauth-db", config_in)

        assert saved[0].config_json == {"host": "no-auth-db.example.com", "port": 5432}

    def test_static_file_connection_is_not_encrypted(self):
        """static_file connections have no password — ensure they work untouched."""
        store = _make_store()
        saved: list[Connection] = []
        repo = MagicMock()
        repo.save.side_effect = lambda c: saved.append(c) or c

        service = ConnectionService(repo=repo, secret_store=store)
        service.create_static_file_connection("tenant-1", "proj-1", "My Upload")

        config = saved[0].config_json
        assert "password" not in config
        assert "allowed_extensions" in config
        assert ".csv" in config["allowed_extensions"]
