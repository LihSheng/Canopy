"""Domain models for the universal connector framework.

Defines:
- ConnectorTypeCategory, ConnectorStatus, ActionPermissionScope, ActionOutcome: enums
- ConnectorContract: unified connector contract covering read and action operations
- ActionContract: stable shape for all connector action types
- is_valid_idempotency_key: validation rule for idempotency keys
"""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum


class ConnectorTypeCategory(StrEnum):
    """Categories of connector source types."""

    DATABASE = "database"
    API = "api"
    FILE = "file"
    OTHER = "other"


class ConnectorStatus(StrEnum):
    """Operational status of a connector in the registry."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    DEGRADED = "degraded"
    PENDING = "pending"


class ActionPermissionScope(StrEnum):
    """Permission scopes that can be granted to a connector action.

    Each connector's action_scope defines which scopes are allowed.
    Actions that request a scope outside that list are rejected.
    """

    READ = "read"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ADMIN = "admin"


class ActionOutcome(StrEnum):
    """Possible outcomes of a connector action execution.

    Used in audit trails and action result tracking.
    """

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class ActionContract:
    """Stable contract shape for all connector action types.

    Every action — read, create, update, delete, or webhook-triggered —
    uses this contract. It carries the permission scope, input schema,
    idempotency key for dedup, audit metadata, and outcome state.

    Parameters
    ----------
    action_type : str
        The kind of action (e.g. "create_record", "update_record", "delete_record").
    permission_scope : str
        The required permission scope (default ActionPermissionScope.READ).
    input_schema : dict
        JSON Schema describing the expected input payload.
    idempotency_key : str or None
        Unique key for safe retry. Must pass is_valid_idempotency_key if set.
    audit_metadata : dict
        Free-form metadata for audit trails (actor, reason, source IP, etc.).
    outcome : str or None
        Result of execution: pending, approved, rejected, completed, failed.
    outcome_detail : str or None
        Human-readable detail about the outcome (error message, reason, etc.).
    """

    action_type: str
    permission_scope: str = ActionPermissionScope.READ.value
    input_schema: dict = field(default_factory=dict)
    idempotency_key: str | None = None
    audit_metadata: dict = field(default_factory=dict)
    outcome: str | None = None
    outcome_detail: str | None = None


@dataclass
class ConnectorContract:
    """Unified connector contract covering read and action operations.

    One contract shape that represents a connector in the tenant-aware registry.
    All connector adapters (JDBC, REST, file, etc.) use this shape.

    The registry stores:
    - type and type_category: what kind of source this is
    - config_json: connection configuration (host, port, etc.)
    - credentials_json: encrypted secrets (password, api_key, token, etc.)
    - action_scope: list of allowed ActionPermissionScope values
    - tenant_id: tenant ownership
    - status: operational health state
    - metadata_json: queryable operational metadata for UI and operator flows
    """

    id: str
    tenant_id: str
    type: str
    name: str
    type_category: str = ConnectorTypeCategory.OTHER.value
    config_json: dict = field(default_factory=dict)
    credentials_json: dict = field(default_factory=dict)
    action_scope: list[str] = field(default_factory=list)
    status: str = ConnectorStatus.ACTIVE.value
    metadata_json: dict = field(default_factory=dict)
    description: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


def is_valid_idempotency_key(key: str | None) -> bool:
    """Validate an idempotency key follows the expected format.

    Rules:
    - None is valid (idempotency not requested).
    - Must be a non-empty string.
    - Max 255 characters.
    - Only printable ASCII characters (code points 32–126).

    Parameters
    ----------
    key : str or None
        The idempotency key to validate.

    Returns
    -------
    bool
        True if the key is valid or None.
    """
    if key is None:
        return True
    if not isinstance(key, str):
        return False
    if not key or len(key) > 255:
        return False
    return all(32 <= ord(c) <= 126 for c in key)
