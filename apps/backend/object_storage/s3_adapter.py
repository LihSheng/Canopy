from object_storage.adapter import StorageAdapter, StorageObjectMeta


class S3StorageAdapter(StorageAdapter):
    """
    Production S3-compatible object storage adapter.

    Uses boto3 to interact with S3 or S3-compatible services.
    Bucket name is configured per environment.
    All operations are tenant-scoped via key prefixes.

    Not yet implemented — this skeleton provides the full interface shape.
    """

    def __init__(self, bucket_name: str, region: str = "us-east-1"):
        self._bucket_name = bucket_name
        self._region = region

    def put_object(
        self,
        key: str,
        data: bytes,
        mime_type: str | None = None,
        tenant_id: str | None = None,
    ) -> StorageObjectMeta:
        """Store object in S3 with immutable check via object existence + lifecycle state."""
        raise NotImplementedError("S3 adapter is not yet implemented")

    def get_object(self, key: str, tenant_id: str | None = None) -> bytes:
        """Retrieve object bytes from S3 with optional checksum verification."""
        raise NotImplementedError("S3 adapter is not yet implemented")

    def delete_object(self, key: str, tenant_id: str | None = None) -> None:
        """Delete object from S3 including any versioned copies."""
        raise NotImplementedError("S3 adapter is not yet implemented")

    def list_objects(self, prefix: str, tenant_id: str | None = None) -> list[StorageObjectMeta]:
        """List S3 objects matching a prefix, returning metadata for each."""
        raise NotImplementedError("S3 adapter is not yet implemented")

    def object_exists(self, key: str, tenant_id: str | None = None) -> bool:
        """Check if an S3 object exists."""
        raise NotImplementedError("S3 adapter is not yet implemented")

    def get_object_meta(self, key: str, tenant_id: str | None = None) -> StorageObjectMeta:
        """Retrieve S3 object metadata without downloading body."""
        raise NotImplementedError("S3 adapter is not yet implemented")

    def set_lifecycle_state(self, key: str, state: str, tenant_id: str | None = None) -> None:
        """Update lifecycle state via S3 object tags or metadata."""
        raise NotImplementedError("S3 adapter is not yet implemented")

    def set_retention_state(self, key: str, state: str, tenant_id: str | None = None) -> None:
        """Update retention state via S3 object tags or metadata."""
        raise NotImplementedError("S3 adapter is not yet implemented")
