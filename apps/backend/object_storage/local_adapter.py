import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from object_storage.adapter import StorageAdapter, StorageObjectMeta
from object_storage.errors import (
    ChecksumMismatchError,
    ObjectImmutableError,
    ObjectNotFoundError,
)


class LocalStorageAdapter(StorageAdapter):
    def __init__(self, root_dir: str | Path, bucket_name: str = "dev-bucket"):
        self._root = Path(root_dir)
        self._bucket_name = bucket_name

    def _full_path(self, key: str) -> Path:
        return self._root / key

    def _meta_path(self, key: str) -> Path:
        return self._root / f"{key}.meta.json"

    def _compute_checksum(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def _load_meta(self, key: str) -> StorageObjectMeta:
        meta_path = self._meta_path(key)
        if not meta_path.exists():
            raise ObjectNotFoundError(key)
        raw = json.loads(meta_path.read_text(encoding="utf-8"))
        raw["created_at"] = datetime.fromisoformat(raw["created_at"])
        if raw.get("updated_at"):
            raw["updated_at"] = datetime.fromisoformat(raw["updated_at"])
        return StorageObjectMeta(**raw)

    def _save_meta(self, meta: StorageObjectMeta) -> None:
        meta_path = self._meta_path(meta.storage_key)
        meta_path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "tenant_id": meta.tenant_id,
            "storage_key": meta.storage_key,
            "checksum": meta.checksum,
            "mime_type": meta.mime_type,
            "size_bytes": meta.size_bytes,
            "lifecycle_state": meta.lifecycle_state,
            "retention_state": meta.retention_state,
            "created_at": meta.created_at.isoformat(),
            "updated_at": meta.updated_at.isoformat() if meta.updated_at else None,
        }
        meta_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def put_object(
        self,
        key: str,
        data: bytes,
        mime_type: str | None = None,
        tenant_id: str | None = None,
    ) -> StorageObjectMeta:
        file_path = self._full_path(key)

        if file_path.exists():
            try:
                existing = self._load_meta(key)
                if existing.lifecycle_state == "active":
                    raise ObjectImmutableError(key)
            except ObjectNotFoundError:
                pass

        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)

        checksum = self._compute_checksum(data)
        now = datetime.now(UTC)
        meta = StorageObjectMeta(
            tenant_id=tenant_id or "",
            storage_key=key,
            checksum=checksum,
            mime_type=mime_type,
            size_bytes=len(data),
            lifecycle_state="active",
            retention_state="retained",
            created_at=now,
        )
        self._save_meta(meta)
        return meta

    def get_object(self, key: str, tenant_id: str | None = None) -> bytes:
        file_path = self._full_path(key)
        if not file_path.exists():
            raise ObjectNotFoundError(key)
        data = file_path.read_bytes()
        meta = self._load_meta(key)
        if meta.checksum:
            actual = self._compute_checksum(data)
            if actual != meta.checksum:
                raise ChecksumMismatchError(key, meta.checksum, actual)
        return data

    def delete_object(self, key: str, tenant_id: str | None = None) -> None:
        file_path = self._full_path(key)
        meta_path = self._meta_path(key)

        if not file_path.exists() and not meta_path.exists():
            raise ObjectNotFoundError(key)

        if file_path.exists():
            file_path.unlink()
        if meta_path.exists():
            meta_path.unlink()

        parent = file_path.parent
        while parent != self._root and parent.exists():
            try:
                next_parent = parent.parent
                parent.rmdir()
                parent = next_parent
            except OSError:
                break

    def list_objects(
        self, prefix: str, tenant_id: str | None = None
    ) -> list[StorageObjectMeta]:
        results: list[StorageObjectMeta] = []
        prefix_path = self._root / prefix

        if not self._root.exists():
            return results

        search_root = prefix_path if prefix_path.is_dir() else prefix_path.parent
        if not search_root.exists():
            return results

        for dirpath, _dirnames, filenames in os.walk(search_root):
            for filename in filenames:
                if filename.endswith(".meta.json"):
                    continue
                full_path = Path(dirpath) / filename
                relative_key = str(full_path.relative_to(self._root)).replace(
                    os.sep, "/"
                )
                if relative_key.startswith(prefix):
                    try:
                        meta = self._load_meta(relative_key)
                        results.append(meta)
                    except ObjectNotFoundError:
                        continue

        return results

    def object_exists(self, key: str, tenant_id: str | None = None) -> bool:
        return self._full_path(key).exists()

    def get_object_meta(
        self, key: str, tenant_id: str | None = None
    ) -> StorageObjectMeta:
        if not self._full_path(key).exists():
            raise ObjectNotFoundError(key)
        return self._load_meta(key)

    def set_lifecycle_state(
        self, key: str, state: str, tenant_id: str | None = None
    ) -> None:
        if not self._full_path(key).exists():
            raise ObjectNotFoundError(key)
        meta = self._load_meta(key)
        meta.lifecycle_state = state
        meta.updated_at = datetime.now(UTC)
        self._save_meta(meta)

    def set_retention_state(
        self, key: str, state: str, tenant_id: str | None = None
    ) -> None:
        if not self._full_path(key).exists():
            raise ObjectNotFoundError(key)
        meta = self._load_meta(key)
        meta.retention_state = state
        meta.updated_at = datetime.now(UTC)
        self._save_meta(meta)

