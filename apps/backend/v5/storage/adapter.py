from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class StorageObjectMeta:
    tenant_id: str
    storage_key: str
    checksum: str | None
    mime_type: str | None
    size_bytes: int
    lifecycle_state: str = "active"
    retention_state: str = "retained"
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime | None = None


@dataclass
class StorageAccessScope:
    tenant_id: str
    is_admin: bool = False
    data_category: str | None = None


class StorageAdapter(ABC):
    @abstractmethod
    def put_object(
        self,
        key: str,
        data: bytes,
        mime_type: str | None = None,
        tenant_id: str | None = None,
    ) -> StorageObjectMeta:
        ...

    @abstractmethod
    def get_object(self, key: str, tenant_id: str | None = None) -> bytes:
        ...

    @abstractmethod
    def delete_object(self, key: str, tenant_id: str | None = None) -> None:
        ...

    @abstractmethod
    def list_objects(
        self, prefix: str, tenant_id: str | None = None
    ) -> list[StorageObjectMeta]:
        ...

    @abstractmethod
    def object_exists(self, key: str, tenant_id: str | None = None) -> bool:
        ...

    @abstractmethod
    def get_object_meta(
        self, key: str, tenant_id: str | None = None
    ) -> StorageObjectMeta:
        ...

    @abstractmethod
    def set_lifecycle_state(
        self, key: str, state: str, tenant_id: str | None = None
    ) -> None:
        ...

    @abstractmethod
    def set_retention_state(
        self, key: str, state: str, tenant_id: str | None = None
    ) -> None:
        ...
