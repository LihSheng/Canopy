import tempfile
from pathlib import Path

import pytest

from v5.storage.access_guard import StorageAccessGuard
from v5.storage.adapter import StorageAccessScope
from v5.storage.errors import ObjectImmutableError, StorageAccessError
from v5.storage.key_generator import generate_object_key
from v5.storage.local_adapter import LocalStorageAdapter
from v5.storage.service import StorageService


@pytest.fixture
def temp_root():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def local_adapter(temp_root):
    return LocalStorageAdapter(root_dir=temp_root)


@pytest.fixture
def storage_service(local_adapter):
    return StorageService(adapter=local_adapter, guard=StorageAccessGuard())


class TestStorageIsolation:
    def test_upload_tenant_a_key_contains_tenant_a_prefix(self, storage_service):
        meta = storage_service.upload_file(
            tenant_id="aaaaaaaa-1111-aaaa-aaaa-aaaaaaaaaaaa",
            data_category="raw",
            filename="test.csv",
            data=b"tenant A data",
        )
        assert "tenants/aaaaaaaa-1111-aaaa-aaaa-aaaaaaaaaaaa" in meta.storage_key
        assert "/raw/" in meta.storage_key

    def test_upload_tenant_b_key_isolated_from_tenant_a(self, storage_service):
        meta_a = storage_service.upload_file(
            tenant_id="aaaaaaaa-1111-aaaa-aaaa-aaaaaaaaaaaa",
            data_category="raw",
            filename="data.csv",
            data=b"tenant A",
        )
        meta_b = storage_service.upload_file(
            tenant_id="bbbbbbbb-2222-bbbb-bbbb-bbbbbbbbbbbb",
            data_category="raw",
            filename="data.csv",
            data=b"tenant B",
        )
        assert "aaaaaaaa-1111-aaaa-aaaa-aaaaaaaaaaaa" in meta_a.storage_key
        assert "bbbbbbbb-2222-bbbb-bbbb-bbbbbbbbbbbb" in meta_b.storage_key
        assert meta_a.storage_key != meta_b.storage_key

    def test_cannot_read_tenant_b_file_as_tenant_a(self, storage_service):
        meta = storage_service.upload_file(
            tenant_id="bbbbbbbb-2222-bbbb-bbbb-bbbbbbbbbbbb",
            data_category="raw",
            filename="secret.csv",
            data=b"tenant B secret",
        )
        with pytest.raises(StorageAccessError, match="Access denied"):
            storage_service.download_file(
                tenant_id="aaaaaaaa-1111-aaaa-aaaa-aaaaaaaaaaaa",
                key=meta.storage_key,
            )

    def test_checksum_roundtrip(self, storage_service):
        original = b"Hello, this is test content for checksum verification."
        meta = storage_service.upload_file(
            tenant_id="aaaaaaaa-1111-aaaa-aaaa-aaaaaaaaaaaa",
            data_category="raw",
            filename="checksum_test.txt",
            data=original,
        )
        assert meta.checksum is not None
        assert len(meta.checksum) == 64

        downloaded = storage_service.download_file(
            tenant_id="aaaaaaaa-1111-aaaa-aaaa-aaaaaaaaaaaa",
            key=meta.storage_key,
        )
        assert downloaded == original

    def test_immutable_upload_second_upload_fails(self, storage_service, local_adapter):
        tid = "cccccccc-3333-cccc-cccc-cccccccccccc"
        key = f"tenants/{tid}/raw/immutable.csv"

        meta1 = local_adapter.put_object(key=key, data=b"first write", tenant_id=tid)
        assert meta1.lifecycle_state == "active"

        with pytest.raises(ObjectImmutableError, match="immutable"):
            local_adapter.put_object(key=key, data=b"second write should fail", tenant_id=tid)

    def test_upload_different_filenames_ok(self, storage_service):
        tid = "dddddddd-4444-dddd-dddd-dddddddddddd"
        meta1 = storage_service.upload_file(
            tenant_id=tid,
            data_category="raw",
            filename="file1.csv",
            data=b"first",
        )
        meta2 = storage_service.upload_file(
            tenant_id=tid,
            data_category="raw",
            filename="file2.csv",
            data=b"second",
        )
        assert meta1.storage_key != meta2.storage_key
        assert meta1.size_bytes == 5
        assert meta2.size_bytes == 6

    def test_lifecycle_archive_then_still_readable(self, storage_service):
        tid = "eeeeeeee-5555-eeee-eeee-eeeeeeeeeeee"
        meta = storage_service.upload_file(
            tenant_id=tid,
            data_category="raw",
            filename="archive_test.csv",
            data=b"archivable content",
        )
        storage_service.archive_object(tenant_id=tid, key=meta.storage_key)

        data = storage_service.download_file(tenant_id=tid, key=meta.storage_key)
        assert data == b"archivable content"

    def test_lifecycle_expire_makes_deletable(self, storage_service):
        tid = "ffffffff-6666-ffff-ffff-ffffffffffff"
        meta = storage_service.upload_file(
            tenant_id=tid,
            data_category="raw",
            filename="expire_test.csv",
            data=b"expirable content",
        )
        storage_service.expire_object(tenant_id=tid, key=meta.storage_key)

        meta_after = storage_service._adapter.get_object_meta(key=meta.storage_key)
        assert meta_after.lifecycle_state == "expired"
        assert meta_after.retention_state == "deletable"

    def test_cleanup_removes_expired_keeps_active_archived(self, storage_service):
        tid = "11111111-7777-1111-1111-111111111111"

        active_meta = storage_service.upload_file(
            tenant_id=tid, data_category="raw", filename="active.csv", data=b"active"
        )
        archived_meta = storage_service.upload_file(
            tenant_id=tid, data_category="raw", filename="archived.csv", data=b"archived"
        )
        expired_meta = storage_service.upload_file(
            tenant_id=tid, data_category="raw", filename="expired.csv", data=b"expired"
        )

        storage_service.archive_object(tenant_id=tid, key=archived_meta.storage_key)
        storage_service.expire_object(tenant_id=tid, key=expired_meta.storage_key)

        count = storage_service.cleanup_expired(tenant_id=tid)
        assert count == 1

        assert storage_service._adapter.object_exists(key=active_meta.storage_key)
        assert storage_service._adapter.object_exists(key=archived_meta.storage_key)
        assert not storage_service._adapter.object_exists(key=expired_meta.storage_key)

    def test_cross_tenant_list_isolation(self, storage_service):
        tid_a = "aaaaaaaa-8888-aaaa-aaaa-aaaaaaaaaaaa"
        tid_b = "bbbbbbbb-8888-bbbb-bbbb-bbbbbbbbbbbb"

        storage_service.upload_file(
            tenant_id=tid_a, data_category="raw", filename="a_file.csv", data=b"A"
        )
        storage_service.upload_file(
            tenant_id=tid_b, data_category="raw", filename="b_file.csv", data=b"B"
        )

        a_files = storage_service.list_tenant_files(tenant_id=tid_a)
        b_files = storage_service.list_tenant_files(tenant_id=tid_b)

        assert all(tid_a in obj.storage_key for obj in a_files)
        assert all(tid_b in obj.storage_key for obj in b_files)
        assert all(tid_b not in obj.storage_key for obj in a_files)
        assert all(tid_a not in obj.storage_key for obj in b_files)

    def test_cross_tenant_access_regression(self, storage_service):
        tid_a = "aaaaaaaa-9999-aaaa-aaaa-aaaaaaaaaaaa"
        tid_b = "bbbbbbbb-9999-bbbb-bbbb-bbbbbbbbbbbb"

        meta_a = storage_service.upload_file(
            tenant_id=tid_a, data_category="raw", filename="secret_a.csv", data=b"secret A"
        )
        meta_b = storage_service.upload_file(
            tenant_id=tid_b, data_category="raw", filename="secret_b.csv", data=b"secret B"
        )

        with pytest.raises(StorageAccessError):
            storage_service.download_file(tenant_id=tid_a, key=meta_b.storage_key)

        with pytest.raises(StorageAccessError):
            storage_service.download_file(tenant_id=tid_b, key=meta_a.storage_key)

        with pytest.raises(StorageAccessError):
            storage_service.delete_file(tenant_id=tid_a, key=meta_b.storage_key)

        with pytest.raises(StorageAccessError):
            storage_service.delete_file(tenant_id=tid_b, key=meta_a.storage_key)

    def test_metadata_stored_correctly(self, storage_service):
        meta = storage_service.upload_file(
            tenant_id="cccccccc-0000-cccc-cccc-cccccccccccc",
            data_category="raw",
            filename="meta_test.csv",
            data=b"metadata test content",
            mime_type="text/csv",
        )
        assert meta.tenant_id == "cccccccc-0000-cccc-cccc-cccccccccccc"
        assert meta.mime_type == "text/csv"
        assert meta.size_bytes == 21
        assert meta.lifecycle_state == "active"
        assert meta.retention_state == "retained"
        assert meta.checksum is not None
        assert meta.created_at is not None

    def test_object_exists_and_get_meta(self, storage_service):
        meta = storage_service.upload_file(
            tenant_id="dddddddd-0000-dddd-dddd-dddddddddddd",
            data_category="raw",
            filename="exists_test.csv",
            data=b"existence check",
        )
        assert storage_service._adapter.object_exists(key=meta.storage_key)

        fetched_meta = storage_service._adapter.get_object_meta(key=meta.storage_key)
        assert fetched_meta.checksum == meta.checksum
        assert fetched_meta.size_bytes == meta.size_bytes

    def test_delete_object_removes_file(self, storage_service):
        meta = storage_service.upload_file(
            tenant_id="eeeeeeee-0000-eeee-eeee-eeeeeeeeeeee",
            data_category="raw",
            filename="delete_test.csv",
            data=b"to be deleted",
        )
        assert storage_service._adapter.object_exists(key=meta.storage_key)

        storage_service.delete_file(tenant_id="eeeeeeee-0000-eeee-eeee-eeeeeeeeeeee", key=meta.storage_key)
        assert not storage_service._adapter.object_exists(key=meta.storage_key)

    def test_put_object_with_same_key_after_expiry_allowed(self, storage_service, temp_root):
        tid = "ffffffff-0000-ffff-ffff-ffffffffffff"
        key = f"tenants/{tid}/raw/reuse_test/data.csv"

        adapter = storage_service._adapter
        meta1 = adapter.put_object(
            key=key, data=b"first write", tenant_id=tid
        )
        adapter.set_lifecycle_state(key, "expired")
        adapter.set_retention_state(key, "deletable")
        adapter.delete_object(key=key)

        meta2 = adapter.put_object(
            key=key, data=b"second write", tenant_id=tid
        )
        assert meta1.storage_key == meta2.storage_key
        assert adapter.get_object(key=key) == b"second write"

    def test_admin_can_bypass_tenant_restrictions(self, local_adapter, temp_root):
        tid_a = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        tid_b = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

        adapter = local_adapter
        adapter.put_object(
            key=f"tenants/{tid_a}/raw/a.csv", data=b"A", tenant_id=tid_a
        )
        adapter.put_object(
            key=f"tenants/{tid_b}/raw/b.csv", data=b"B", tenant_id=tid_b
        )

        guard = StorageAccessGuard()
        admin_scope = StorageAccessScope(tenant_id="admin-user", is_admin=True)

        assert guard.check_write_access(f"tenants/{tid_a}/raw/a.csv", admin_scope) is True
        assert guard.check_write_access(f"tenants/{tid_b}/raw/b.csv", admin_scope) is True
        assert guard.check_delete_access(f"tenants/{tid_a}/raw/a.csv", admin_scope) is True
        assert guard.check_delete_access(f"tenants/{tid_b}/raw/b.csv", admin_scope) is True

    def test_upload_to_different_categories_separated(self, storage_service):
        tid = "aaaa0000-1111-aaaa-aaaa-aaaaaaaaaaaa"
        raw_meta = storage_service.upload_file(
            tenant_id=tid, data_category="raw", filename="data.csv", data=b"raw"
        )
        clean_meta = storage_service.upload_file(
            tenant_id=tid, data_category="clean", filename="data.csv", data=b"clean"
        )
        assert "/raw/" in raw_meta.storage_key
        assert "/clean/" in clean_meta.storage_key
        assert raw_meta.storage_key != clean_meta.storage_key

    def test_list_objects_empty_directory(self, storage_service, local_adapter):
        results = local_adapter.list_objects(prefix="tenants/nonexistent/")
        assert results == []

    def test_list_objects_with_multiple_files(self, storage_service, local_adapter, temp_root):
        tid = "list-test-tid-123456789-abcdef123456"
        adapter = local_adapter

        adapter.put_object(
            key=f"tenants/{tid}/raw/file1.csv", data=b"f1", tenant_id=tid
        )
        adapter.put_object(
            key=f"tenants/{tid}/raw/file2.csv", data=b"f2", tenant_id=tid
        )
        adapter.put_object(
            key=f"tenants/{tid}/clean/file3.csv", data=b"f3", tenant_id=tid
        )

        all_results = adapter.list_objects(prefix=f"tenants/{tid}/")
        assert len(all_results) == 3

        raw_results = adapter.list_objects(prefix=f"tenants/{tid}/raw/")
        assert len(raw_results) == 2

        clean_results = adapter.list_objects(prefix=f"tenants/{tid}/clean/")
        assert len(clean_results) == 1
