import pytest

from object_storage.key_generator import (
    generate_object_key,
    generate_tenant_prefix,
    parse_category_from_key,
    parse_tenant_from_key,
    validate_key_for_tenant,
)
from object_storage.errors import TenantPrefixError


class TestGenerateTenantPrefix:
    def test_returns_correct_format(self):
        result = generate_tenant_prefix("abc-123")
        assert result == "tenants/abc-123"

    def test_uuid_tenant_id(self):
        tid = "12345678-1234-1234-1234-123456789abc"
        result = generate_tenant_prefix(tid)
        assert result == f"tenants/{tid}"

    def test_empty_tenant_id(self):
        result = generate_tenant_prefix("")
        assert result == "tenants/"


class TestGenerateObjectKey:
    def test_includes_all_components(self):
        key = generate_object_key(
            "tenant-1", "raw", "data.csv", use_uuid_subdir=False
        )
        assert key.startswith("tenants/tenant-1/raw/")
        assert key.endswith("/data.csv")

    def test_invalid_category_raises(self):
        with pytest.raises(ValueError, match="Invalid data_category"):
            generate_object_key("t1", "invalid", "file.txt")

    def test_valid_categories_accepted(self):
        for category in ("raw", "clean", "exports", "metadata"):
            key = generate_object_key("t1", category, "f.txt", use_uuid_subdir=False)
            assert f"/{category}/" in key

    def test_uuid_subdirectory_unique(self):
        key1 = generate_object_key("t1", "raw", "data.csv")
        key2 = generate_object_key("t1", "raw", "data.csv")
        assert key1 != key2

    def test_different_categories_different_segments(self):
        raw_key = generate_object_key("t1", "raw", "f.txt", use_uuid_subdir=False)
        clean_key = generate_object_key("t1", "clean", "f.txt", use_uuid_subdir=False)
        assert "/raw/" in raw_key
        assert "/clean/" in clean_key
        assert raw_key != clean_key

    def test_different_tenants_have_different_prefixes(self):
        key_a = generate_object_key("tenant-A", "raw", "f.txt", use_uuid_subdir=False)
        key_b = generate_object_key("tenant-B", "raw", "f.txt", use_uuid_subdir=False)
        assert key_a != key_b
        assert "tenant-A" in key_a
        assert "tenant-B" in key_b

    def test_without_uuid_subdir_is_consistent(self):
        key1 = generate_object_key("t1", "raw", "data.csv", use_uuid_subdir=False)
        key2 = generate_object_key("t1", "raw", "data.csv", use_uuid_subdir=False)
        assert key1 == key2


class TestParseTenantFromKey:
    def test_extracts_tenant_id(self):
        key = "tenants/12345678-1234-1234-1234-123456789abc/raw/data.csv"
        result = parse_tenant_from_key(key)
        assert result == "12345678-1234-1234-1234-123456789abc"

    def test_no_match_returns_none(self):
        result = parse_tenant_from_key("other/prefix/file.txt")
        assert result is None

    def test_malformed_key_returns_none(self):
        result = parse_tenant_from_key("tenants/not-a-uuid/raw/data.csv")
        assert result is None

    def test_short_key_returns_none(self):
        result = parse_tenant_from_key("tenants/")
        assert result is None


class TestParseCategoryFromKey:
    def test_extracts_category(self):
        key = "tenants/12345678-1234-1234-1234-123456789abc/raw/data.csv"
        result = parse_category_from_key(key)
        assert result == "raw"

    def test_extracts_clean_category(self):
        key = "tenants/abc/clean/123/data.csv"
        result = parse_category_from_key(key)
        assert result == "clean"

    def test_no_match_returns_none(self):
        result = parse_category_from_key("tenants/abc/invalid")
        assert result is None

    def test_exports_category(self):
        key = "tenants/t1/exports/report.xlsx"
        result = parse_category_from_key(key)
        assert result == "exports"

    def test_metadata_category(self):
        key = "tenants/t1/metadata/info.json"
        result = parse_category_from_key(key)
        assert result == "metadata"


class TestValidateKeyForTenant:
    def test_matching_tenant_returns_true(self):
        key = "tenants/tenant-A/raw/data.csv"
        assert validate_key_for_tenant(key, "tenant-A") is True

    def test_different_tenant_returns_false(self):
        key = "tenants/tenant-A/raw/data.csv"
        assert validate_key_for_tenant(key, "tenant-B") is False

    def test_partial_match_returns_false(self):
        key = "tenants/tenant-AB/raw/data.csv"
        assert validate_key_for_tenant(key, "tenant-A") is False

    def test_no_tenant_prefix_returns_false(self):
        key = "other/data.csv"
        assert validate_key_for_tenant(key, "tenant-A") is False

    def test_uuid_tenant_validation(self):
        tid = "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"
        key = f"tenants/{tid}/raw/file.txt"
        assert validate_key_for_tenant(key, tid) is True
        assert validate_key_for_tenant(key, "11111111-2222-3333-4444-555555555555") is False

