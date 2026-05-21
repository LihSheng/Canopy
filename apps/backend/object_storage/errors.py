class StorageError(Exception):
    pass


class StorageAccessError(StorageError):
    def __init__(self, key: str, reason: str):
        self.key = key
        self.reason = reason
        super().__init__(f"Access denied for key '{key}': {reason}")


class ObjectImmutableError(StorageError):
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Object '{key}' is immutable and cannot be overwritten")


class ObjectNotFoundError(StorageError):
    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Object not found: '{key}'")


class TenantPrefixError(StorageError):
    def __init__(self, key: str, tenant_id: str):
        self.key = key
        self.tenant_id = tenant_id
        super().__init__(f"Key '{key}' does not belong to tenant '{tenant_id}'")


class ChecksumMismatchError(StorageError):
    def __init__(self, key: str, expected: str, actual: str):
        self.key = key
        self.expected = expected
        self.actual = actual
        super().__init__(f"Checksum mismatch for '{key}': expected {expected}, got {actual}")
