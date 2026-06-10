"""Service for the connector registry — registration, query, credential encryption, and action validation."""

import uuid
from datetime import UTC, datetime

from common.errors import NotFoundError
from connection.secret_store import (
    AesGcmSecretStore,
    SecretStore,
    decrypt_secret_value,
)
from connector.domain import (
    ActionContract,
    ActionPermissionScope,
    ConnectorContract,
    ConnectorStatus,
    is_valid_idempotency_key,
)
from connector.repository import ConnectorRegistryRepository

# Keys in credentials_json that should be encrypted at rest.
_CONNECTOR_CREDENTIAL_KEYS = {
    "password",
    "api_key",
    "token",
    "secret",
    "private_key",
}


class ConnectorRegistryService:
    """Business logic for the connector registry.

    Handles registration, retrieval, status updates, credential encryption,
    action validation, and metadata queries.
    """

    def __init__(
        self,
        repo: ConnectorRegistryRepository,
        secret_store: SecretStore | None = None,
    ):
        self._repo = repo
        self._secret_store = secret_store

    def register(
        self,
        tenant_id: str,
        type_: str,
        name: str,
        config_json: dict | None = None,
        credentials_json: dict | None = None,
        action_scope: list[str] | None = None,
        type_category: str = "",
        description: str = "",
    ) -> ConnectorContract:
        """Register a new connector in the tenant-aware registry.

        Credentials are encrypted before storage.
        """
        now = datetime.now(UTC)
        encrypted_creds = self._encrypt_credentials(credentials_json or {})
        connector = ConnectorContract(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            type=type_,
            name=name,
            type_category=type_category,
            config_json=config_json or {},
            credentials_json=encrypted_creds,
            action_scope=action_scope or [ActionPermissionScope.READ.value],
            status=ConnectorStatus.ACTIVE.value,
            metadata_json={},
            description=description,
            created_at=now,
        )
        return self._repo.save(connector)

    def get(self, id: str, tenant_id: str | None = None) -> ConnectorContract | None:
        """Retrieve a connector by id, optionally tenant-scoped."""
        return self._repo.get(id, tenant_id=tenant_id)

    def list_by_tenant(self, tenant_id: str) -> list[ConnectorContract]:
        """List all connectors for a tenant."""
        return self._repo.list_by_tenant(tenant_id)

    def list_all(self, tenant_id: str | None = None) -> list[ConnectorContract]:
        """List all connectors, optionally filtered by tenant."""
        return self._repo.list_all(tenant_id=tenant_id)

    def update_status(self, id: str, status: str, tenant_id: str | None = None) -> ConnectorContract:
        """Update the operational status of a connector."""
        self._require_connector(id, tenant_id=tenant_id)
        updated = self._repo.update_status(id, status)
        if updated is None:
            raise NotFoundError("Connector not found")
        return updated

    def update_metadata(self, id: str, metadata: dict, tenant_id: str | None = None) -> ConnectorContract:
        """Merge new metadata into a connector's operational metadata.

        Useful for UI and operator flows that need to track health,
        last sync time, etc.
        """
        self._require_connector(id, tenant_id=tenant_id)
        updated = self._repo.update_metadata(id, metadata)
        if updated is None:
            raise NotFoundError("Connector not found")
        return updated

    def delete(self, id: str, tenant_id: str | None = None) -> dict:
        """Remove a connector from the registry."""
        self._require_connector(id, tenant_id=tenant_id)
        deleted = self._repo.delete(id)
        if not deleted:
            raise NotFoundError("Connector not found")
        return {"deleted": True, "id": id}

    def query_metadata(self, tenant_id: str | None = None, **filters) -> list[ConnectorContract]:
        """Query connector metadata for UI and operator flows.

        Returns all connectors for the given tenant, which the caller
        can further filter or shape for presentation.
        """
        return self._repo.list_all(tenant_id=tenant_id)

    def validate_action(self, action: ActionContract, connector: ConnectorContract) -> dict:
        """Validate an action against the connector's contract.

        Checks:
        - The action's permission scope is in the connector's action_scope.
        - The idempotency key is valid if provided.

        Returns
        -------
        dict with keys:
            - valid (bool): whether the action passes validation
            - errors (list[str]): validation error messages
        """
        errors = []

        if action.permission_scope not in connector.action_scope:
            errors.append(
                f"Permission scope '{action.permission_scope}' not in connector action scope: {connector.action_scope}"
            )

        if action.idempotency_key is not None and not is_valid_idempotency_key(action.idempotency_key):
            errors.append("Invalid idempotency key format")

        return {"valid": len(errors) == 0, "errors": errors}

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_connector(self, id: str, tenant_id: str | None = None) -> ConnectorContract:
        connector = self._repo.get(id, tenant_id=tenant_id)
        if connector is None:
            raise NotFoundError("Connector not found")
        return connector

    def _encrypt_credentials(self, credentials: dict) -> dict:
        """Encrypt known sensitive credential keys."""
        result = dict(credentials)
        targets = {
            key: result[key]
            for key in _CONNECTOR_CREDENTIAL_KEYS
            if isinstance(result.get(key), str) and len(result[key]) > 0
        }
        if not targets:
            return result
        store = self._secret_store or self._build_default_store()
        for key in targets:
            result[key] = store.encrypt(result[key])
        return result

    def _decrypt_credentials(self, connector: ConnectorContract) -> dict:
        """Decrypt credential values for use (e.g., during action execution)."""
        creds = dict(connector.credentials_json or {})
        store = self._secret_store or self._build_default_store()
        for key in _CONNECTOR_CREDENTIAL_KEYS:
            value = creds.get(key)
            if value and isinstance(value, str):
                creds[key] = decrypt_secret_value(value, store, allow_legacy_plaintext=True)
        return creds

    @staticmethod
    def _build_default_store() -> SecretStore:
        return AesGcmSecretStore()
