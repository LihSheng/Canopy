"""Tests for connector contract and registry (PRD 0023 item 1).

Covers contract shape, permission scope, idempotency key rules,
credential encryption, audit event shape, and registry persistence.
"""

from unittest.mock import MagicMock

from connection.secret_store import ENCRYPTED_VALUE_PREFIX, AesGcmSecretStore
from connector.domain import (
    ActionContract,
    ActionOutcome,
    ActionPermissionScope,
    ConnectorContract,
    ConnectorStatus,
    ConnectorTypeCategory,
    is_valid_idempotency_key,
)
from connector.service import ConnectorRegistryService

_TEST_KEY = bytes(range(32))


def _make_store() -> AesGcmSecretStore:
    return AesGcmSecretStore(key=_TEST_KEY)


# ---------------------------------------------------------------------------
# ConnectorContract shape — one contract covers read and action operations
# ---------------------------------------------------------------------------


class TestConnectorContractShape:
    """Verify the connector contract covers read and action operations."""

    def test_connector_contract_has_all_required_fields(self):
        contract = ConnectorContract(id="c-1", tenant_id="t-1", type="postgresql", name="My DB")
        assert contract.id == "c-1"
        assert contract.tenant_id == "t-1"
        assert contract.type == "postgresql"
        assert contract.name == "My DB"
        assert contract.type_category == ConnectorTypeCategory.OTHER.value
        assert contract.config_json == {}
        assert contract.credentials_json == {}
        assert contract.action_scope == []
        assert contract.status == ConnectorStatus.ACTIVE.value
        assert contract.metadata_json == {}
        assert contract.description == ""

    def test_connector_contract_defaults_can_be_overridden(self):
        contract = ConnectorContract(
            id="c-2",
            tenant_id="t-1",
            type="rest_api",
            name="API Connector",
            type_category=ConnectorTypeCategory.API.value,
            config_json={"url": "https://api.example.com"},
            credentials_json={"api_key": "enc:..."},
            action_scope=[
                ActionPermissionScope.READ.value,
                ActionPermissionScope.CREATE.value,
            ],
            status=ConnectorStatus.ERROR.value,
            metadata_json={"health": "degraded"},
            description="A REST API connector",
        )
        assert contract.type_category == ConnectorTypeCategory.API.value
        assert contract.config_json == {"url": "https://api.example.com"}
        assert contract.credentials_json == {"api_key": "enc:..."}
        assert contract.action_scope == ["read", "create"]
        assert contract.status == ConnectorStatus.ERROR.value
        assert contract.metadata_json == {"health": "degraded"}
        assert contract.description == "A REST API connector"

    def test_action_contract_has_permission_scope_and_idempotency(self):
        action = ActionContract(
            action_type="create_record",
            permission_scope=ActionPermissionScope.CREATE.value,
            input_schema={
                "type": "object",
                "properties": {"name": {"type": "string"}},
            },
            idempotency_key="idem-001",
            audit_metadata={"actor": "user-1"},
        )
        assert action.action_type == "create_record"
        assert action.permission_scope == "create"
        assert action.input_schema["properties"]["name"]["type"] == "string"
        assert action.idempotency_key == "idem-001"
        assert action.audit_metadata == {"actor": "user-1"}

    def test_action_contract_defaults(self):
        action = ActionContract(action_type="read_data")
        assert action.permission_scope == ActionPermissionScope.READ.value
        assert action.input_schema == {}
        assert action.idempotency_key is None
        assert action.audit_metadata == {}
        assert action.outcome is None

    def test_connector_has_timestamps(self):
        from datetime import datetime

        contract = ConnectorContract(id="c-3", tenant_id="t-1", type="mysql", name="MySQL DB")
        assert isinstance(contract.created_at, datetime)
        assert contract.updated_at is None


# ---------------------------------------------------------------------------
# Idempotency key rules
# ---------------------------------------------------------------------------


class TestIdempotencyKeyValidation:
    def test_valid_key(self):
        assert is_valid_idempotency_key("idem-001") is True

    def test_none_is_valid(self):
        assert is_valid_idempotency_key(None) is True

    def test_empty_string_is_invalid(self):
        assert is_valid_idempotency_key("") is False

    def test_key_too_long_is_invalid(self):
        assert is_valid_idempotency_key("x" * 256) is False

    def test_non_printable_chars_are_invalid(self):
        assert is_valid_idempotency_key("key\nwith\nnewlines") is False

    def test_non_string_is_invalid(self):
        assert is_valid_idempotency_key(12345) is False


# ---------------------------------------------------------------------------
# Permission scope model
# ---------------------------------------------------------------------------


class TestActionPermissionScopes:
    def test_scope_values(self):
        assert ActionPermissionScope.READ.value == "read"
        assert ActionPermissionScope.CREATE.value == "create"
        assert ActionPermissionScope.UPDATE.value == "update"
        assert ActionPermissionScope.DELETE.value == "delete"
        assert ActionPermissionScope.ADMIN.value == "admin"

    def test_action_outcome_values(self):
        assert ActionOutcome.PENDING.value == "pending"
        assert ActionOutcome.APPROVED.value == "approved"
        assert ActionOutcome.REJECTED.value == "rejected"
        assert ActionOutcome.COMPLETED.value == "completed"
        assert ActionOutcome.FAILED.value == "failed"


# ---------------------------------------------------------------------------
# ConnectorRegistryService — contract and registry behavior
# ---------------------------------------------------------------------------


class TestRegistryService:
    def test_register_creates_connector_in_registry(self):
        repo = MagicMock()
        repo.save.return_value = ConnectorContract(
            id="c-1",
            tenant_id="t-1",
            type="postgresql",
            name="My DB",
            action_scope=["read"],
        )
        service = ConnectorRegistryService(repo)
        result = service.register(
            tenant_id="t-1",
            type_="postgresql",
            name="My DB",
            action_scope=["read"],
        )
        assert result.tenant_id == "t-1"
        assert result.type == "postgresql"
        assert result.name == "My DB"
        assert result.action_scope == ["read"]
        repo.save.assert_called_once()

    def test_register_with_credentials_encrypts_them(self):
        store = _make_store()
        repo = MagicMock()

        saved = []
        repo.save.side_effect = lambda c: saved.append(c) or c

        service = ConnectorRegistryService(repo, secret_store=store)
        credentials = {"password": "s3cret!", "api_key": "key-123"}

        service.register(
            tenant_id="t-1",
            type_="postgresql",
            name="My DB",
            credentials_json=credentials,
            action_scope=["read"],
        )

        persisted = saved[0].credentials_json
        assert persisted["password"] != "s3cret!"
        assert persisted["password"].startswith(ENCRYPTED_VALUE_PREFIX)
        assert persisted["api_key"] != "key-123"
        assert persisted["api_key"].startswith(ENCRYPTED_VALUE_PREFIX)
        assert store.decrypt(persisted["password"]) == "s3cret!"
        assert store.decrypt(persisted["api_key"]) == "key-123"

    def test_get_returns_connector(self):
        repo = MagicMock()
        expected = ConnectorContract(id="c-1", tenant_id="t-1", type="postgresql", name="My DB")
        repo.get.return_value = expected

        service = ConnectorRegistryService(repo)
        result = service.get("c-1", tenant_id="t-1")

        assert result is expected
        repo.get.assert_called_with("c-1", tenant_id="t-1")

    def test_get_returns_none_when_not_found(self):
        repo = MagicMock()
        repo.get.return_value = None

        service = ConnectorRegistryService(repo)
        result = service.get("nonexistent", tenant_id="t-1")

        assert result is None

    def test_list_by_tenant_delegates(self):
        repo = MagicMock()
        repo.list_by_tenant.return_value = []

        service = ConnectorRegistryService(repo)
        result = service.list_by_tenant("t-1")

        assert result == []
        repo.list_by_tenant.assert_called_with("t-1")

    def test_update_status_changes_status(self):
        repo = MagicMock()
        connector = ConnectorContract(id="c-1", tenant_id="t-1", type="postgresql", name="My DB")
        repo.get.return_value = connector
        repo.update_status.return_value = ConnectorContract(
            id="c-1",
            tenant_id="t-1",
            type="postgresql",
            name="My DB",
            status=ConnectorStatus.ERROR.value,
        )

        service = ConnectorRegistryService(repo)
        result = service.update_status("c-1", ConnectorStatus.ERROR.value, tenant_id="t-1")

        assert result.status == ConnectorStatus.ERROR.value

    def test_delete_removes_connector(self):
        repo = MagicMock()
        repo.get.return_value = ConnectorContract(id="c-1", tenant_id="t-1", type="postgresql", name="My DB")
        repo.delete.return_value = True

        service = ConnectorRegistryService(repo)
        result = service.delete("c-1", tenant_id="t-1")

        assert result == {"deleted": True, "id": "c-1"}

    def test_validate_action_rejects_wrong_permission_scope(self):
        repo = MagicMock()
        service = ConnectorRegistryService(repo)

        connector = ConnectorContract(
            id="c-1",
            tenant_id="t-1",
            type="postgresql",
            name="My DB",
            action_scope=["read"],
        )
        action = ActionContract(
            action_type="delete_record",
            permission_scope=ActionPermissionScope.DELETE.value,
        )

        result = service.validate_action(action, connector)
        assert result["valid"] is False
        assert any("Permission scope" in e for e in result["errors"])

    def test_validate_action_accepts_valid_scope_and_key(self):
        repo = MagicMock()
        service = ConnectorRegistryService(repo)

        connector = ConnectorContract(
            id="c-1",
            tenant_id="t-1",
            type="postgresql",
            name="My DB",
            action_scope=["read", "create", "update", "delete"],
        )
        action = ActionContract(
            action_type="update_record",
            permission_scope=ActionPermissionScope.UPDATE.value,
            idempotency_key="idem-abc-123",
        )

        result = service.validate_action(action, connector)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_validate_action_invalid_idempotency_key(self):
        repo = MagicMock()
        service = ConnectorRegistryService(repo)

        connector = ConnectorContract(
            id="c-1",
            tenant_id="t-1",
            type="postgresql",
            name="My DB",
            action_scope=["read", "create"],
        )
        action = ActionContract(
            action_type="create_record",
            permission_scope=ActionPermissionScope.CREATE.value,
            idempotency_key="",
        )

        result = service.validate_action(action, connector)
        assert result["valid"] is False

    def test_query_metadata_returns_connectors(self):
        repo = MagicMock()
        repo.list_all.return_value = [
            ConnectorContract(id="c-1", tenant_id="t-1", type="pg", name="DB 1"),
            ConnectorContract(id="c-2", tenant_id="t-1", type="rest", name="API 1"),
        ]

        service = ConnectorRegistryService(repo)
        result = service.query_metadata(tenant_id="t-1")

        assert len(result) == 2
        repo.list_all.assert_called_with(tenant_id="t-1")


# ---------------------------------------------------------------------------
# Registry persistence — integration tests with real Postgres DB
# ---------------------------------------------------------------------------


class TestConnectorRegistryRepository:
    def test_save_and_retrieve(self):
        from tests.unit.postgres_test_db import make_postgres_session

        session = make_postgres_session(("connector.schema",))
        try:
            from connector.repository import ConnectorRegistryRepository

            repo = ConnectorRegistryRepository(session)
            service = ConnectorRegistryService(repo)

            result = service.register(
                tenant_id="t-1",
                type_="postgresql",
                name="Test DB",
                config_json={"host": "localhost", "port": 5432},
                action_scope=["read"],
            )

            fetched = service.get(result.id, tenant_id="t-1")
            assert fetched is not None
            assert fetched.id == result.id
            assert fetched.tenant_id == "t-1"
            assert fetched.type == "postgresql"
            assert fetched.name == "Test DB"
            assert fetched.config_json == {"host": "localhost", "port": 5432}
            assert fetched.action_scope == ["read"]
            assert fetched.status == ConnectorStatus.ACTIVE.value
        finally:
            session.close()

    def test_registry_stores_all_fields(self):
        """Registry stores type, config, encrypted credentials, action scope,
        tenant scope, and status."""
        from tests.unit.postgres_test_db import make_postgres_session

        session = make_postgres_session(("connector.schema",))
        try:
            from connector.repository import ConnectorRegistryRepository

            repo = ConnectorRegistryRepository(session)
            store = _make_store()
            service = ConnectorRegistryService(repo, secret_store=store)

            credentials = {"password": "secret123"}
            result = service.register(
                tenant_id="t-2",
                type_="rest_api",
                name="API Connector",
                config_json={"base_url": "https://api.example.com"},
                credentials_json=credentials,
                action_scope=["read", "create"],
                type_category="api",
                description="My API connector",
            )

            assert result.tenant_id == "t-2"
            assert result.type == "rest_api"
            assert result.name == "API Connector"
            assert result.config_json == {"base_url": "https://api.example.com"}
            assert result.credentials_json["password"].startswith(ENCRYPTED_VALUE_PREFIX)
            assert result.action_scope == ["read", "create"]
            assert result.type_category == "api"
            assert result.status == ConnectorStatus.ACTIVE.value
            assert result.description == "My API connector"

            decrypted = store.decrypt(result.credentials_json["password"])
            assert decrypted == "secret123"
        finally:
            session.close()

    def test_list_by_tenant_returns_only_that_tenants_connectors(self):
        from tests.unit.postgres_test_db import make_postgres_session

        session = make_postgres_session(("connector.schema",))
        try:
            from connector.repository import ConnectorRegistryRepository

            repo = ConnectorRegistryRepository(session)
            store = _make_store()
            service = ConnectorRegistryService(repo, secret_store=store)

            service.register(tenant_id="t-1", type_="postgresql", name="DB 1")
            service.register(tenant_id="t-1", type_="mysql", name="DB 2")
            service.register(tenant_id="t-2", type_="rest_api", name="API 1")

            t1_connectors = service.list_by_tenant("t-1")
            assert len(t1_connectors) == 2

            t2_connectors = service.list_by_tenant("t-2")
            assert len(t2_connectors) == 1
        finally:
            session.close()

    def test_update_status_persists(self):
        from tests.unit.postgres_test_db import make_postgres_session

        session = make_postgres_session(("connector.schema",))
        try:
            from connector.repository import ConnectorRegistryRepository

            repo = ConnectorRegistryRepository(session)
            service = ConnectorRegistryService(repo)

            result = service.register(tenant_id="t-1", type_="postgresql", name="My DB")
            assert result.status == ConnectorStatus.ACTIVE.value

            updated = service.update_status(result.id, ConnectorStatus.ERROR.value, tenant_id="t-1")
            assert updated.status == ConnectorStatus.ERROR.value

            fetched = service.get(result.id, tenant_id="t-1")
            assert fetched is not None
            assert fetched.status == ConnectorStatus.ERROR.value
        finally:
            session.close()

    def test_delete_removes_from_registry(self):
        from tests.unit.postgres_test_db import make_postgres_session

        session = make_postgres_session(("connector.schema",))
        try:
            from connector.repository import ConnectorRegistryRepository

            repo = ConnectorRegistryRepository(session)
            service = ConnectorRegistryService(repo)

            result = service.register(tenant_id="t-1", type_="postgresql", name="My DB")
            assert service.get(result.id, tenant_id="t-1") is not None

            service.delete(result.id, tenant_id="t-1")
            assert service.get(result.id, tenant_id="t-1") is None
        finally:
            session.close()

    def test_query_metadata_returns_all_fields_for_ui(self):
        from tests.unit.postgres_test_db import make_postgres_session

        session = make_postgres_session(("connector.schema",))
        try:
            from connector.repository import ConnectorRegistryRepository

            repo = ConnectorRegistryRepository(session)
            service = ConnectorRegistryService(repo)

            service.register(
                tenant_id="t-1",
                type_="postgresql",
                name="Prod DB",
                config_json={"host": "prod.example.com"},
                action_scope=["read"],
            )

            connectors = service.query_metadata(tenant_id="t-1")
            assert len(connectors) == 1
            c = connectors[0]
            assert c.name == "Prod DB"
            assert c.type == "postgresql"
            assert c.status == ConnectorStatus.ACTIVE.value
            assert c.action_scope == ["read"]
        finally:
            session.close()

    def test_update_metadata_persists(self):
        from tests.unit.postgres_test_db import make_postgres_session

        session = make_postgres_session(("connector.schema",))
        try:
            from connector.repository import ConnectorRegistryRepository

            repo = ConnectorRegistryRepository(session)
            service = ConnectorRegistryService(repo)

            result = service.register(tenant_id="t-1", type_="postgresql", name="My DB")

            updated = service.update_metadata(
                result.id,
                {"health": "ok", "last_sync": "2026-06-01T00:00:00Z"},
                tenant_id="t-1",
            )
            assert updated.metadata_json == {
                "health": "ok",
                "last_sync": "2026-06-01T00:00:00Z",
            }

            fetched = service.get(result.id, tenant_id="t-1")
            assert fetched is not None
            assert fetched.metadata_json["health"] == "ok"
            assert fetched.metadata_json["last_sync"] == "2026-06-01T00:00:00Z"
        finally:
            session.close()

    def test_registry_handles_multiple_connector_types(self):
        """JDBC, REST, and file connectors all use the same registry contract."""
        from tests.unit.postgres_test_db import make_postgres_session

        session = make_postgres_session(("connector.schema",))
        try:
            from connector.repository import ConnectorRegistryRepository

            repo = ConnectorRegistryRepository(session)
            service = ConnectorRegistryService(repo)

            # JDBC connector
            jdbc = service.register(
                tenant_id="t-1",
                type_="postgresql",
                name="JDBC DB",
                config_json={"host": "db.local"},
                action_scope=["read"],
            )

            # REST connector
            rest = service.register(
                tenant_id="t-1",
                type_="rest_api",
                name="REST API",
                config_json={"base_url": "https://api.local"},
                action_scope=["read", "create"],
            )

            # File connector
            file_c = service.register(
                tenant_id="t-1",
                type_="static_file",
                name="File Source",
                config_json={"path": "/data/file.csv"},
                action_scope=["read"],
            )

            assert jdbc.type == "postgresql"
            assert rest.type == "rest_api"
            assert file_c.type == "static_file"
            assert len(service.list_by_tenant("t-1")) == 3
        finally:
            session.close()
