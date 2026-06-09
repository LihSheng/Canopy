"""Connector domain — contract, registry, and action models.

This module provides the universal connector framework foundation:
- ConnectorContract: unified contract covering read and action operations
- ActionContract: stable shape for all connector action types
- ConnectorRegistry: tenant-aware storage for connector state
- Permission scope model for action authorization
- Idempotency key rules for safe retries
"""

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

__all__ = [
    "ActionContract",
    "ActionOutcome",
    "ActionPermissionScope",
    "ConnectorContract",
    "ConnectorRegistryService",
    "ConnectorStatus",
    "ConnectorTypeCategory",
    "is_valid_idempotency_key",
]
