import re
from uuid import uuid4

_VALID_DATA_CATEGORIES = frozenset({"raw", "clean", "exports", "metadata"})

_TENANT_KEY_PATTERN = re.compile(r"^tenants/([a-f0-9-]{36})/")
_CATEGORY_PATTERN = re.compile(r"^tenants/([^/]+)/([a-z_]+)/")


def generate_tenant_prefix(tenant_id: str) -> str:
    return f"tenants/{tenant_id}"


def generate_object_key(tenant_id: str, data_category: str, filename: str, *, use_uuid_subdir: bool = True) -> str:
    if data_category not in _VALID_DATA_CATEGORIES:
        raise ValueError(f"Invalid data_category '{data_category}'. Must be one of: {sorted(_VALID_DATA_CATEGORIES)}")
    if use_uuid_subdir:
        return f"tenants/{tenant_id}/{data_category}/{uuid4()}/{filename}"
    return f"tenants/{tenant_id}/{data_category}/{filename}"


def parse_tenant_from_key(key: str) -> str | None:
    match = _TENANT_KEY_PATTERN.match(key)
    if match:
        return match.group(1)
    return None


def parse_category_from_key(key: str) -> str | None:
    match = _CATEGORY_PATTERN.match(key)
    if match:
        return match.group(2)
    return None


def validate_key_for_tenant(key: str, tenant_id: str) -> bool:
    expected_prefix = f"tenants/{tenant_id}/"
    return key.startswith(expected_prefix)
