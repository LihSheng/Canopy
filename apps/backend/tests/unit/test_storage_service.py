from unittest.mock import MagicMock

import pytest

from object_storage.adapter import StorageObjectMeta
from object_storage.errors import StorageAccessError
from object_storage.service import StorageService


class TestStorageServiceUpload:
    def test_upload_generates_correct_key_and_returns_metadata(self):
        mock_adapter = MagicMock()
        mock_guard = MagicMock()
        mock_guard.check_write_access.return_value = True

        expected_meta = StorageObjectMeta(
            tenant_id="tenant-A",
            storage_key="tenants/tenant-A/raw/test-uuid/data.csv",
            checksum="abc123",
            mime_type="text/csv",
            size_bytes=100,
        )
        mock_adapter.put_object.return_value = expected_meta

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        result = service.upload_file(
            tenant_id="tenant-A",
            data_category="raw",
            filename="data.csv",
            data=b"test data",
            mime_type="text/csv",
        )

        assert result == expected_meta
        mock_adapter.put_object.assert_called_once()
        call_args = mock_adapter.put_object.call_args
        assert call_args.kwargs["tenant_id"] == "tenant-A"
        assert call_args.kwargs["mime_type"] == "text/csv"
        assert call_args.kwargs["data"] == b"test data"
        assert "tenant-A" in call_args.kwargs["key"]
        assert "/raw/" in call_args.kwargs["key"]

    def test_upload_fails_with_wrong_tenant(self):
        mock_adapter = MagicMock()
        mock_guard = MagicMock()
        mock_guard.check_write_access.side_effect = StorageAccessError("key", "wrong tenant")

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        with pytest.raises(StorageAccessError):
            service.upload_file(
                tenant_id="tenant-B",
                data_category="raw",
                filename="data.csv",
                data=b"test",
            )

    def test_upload_admin_can_write(self):
        mock_adapter = MagicMock()
        mock_guard = MagicMock()
        mock_guard.check_write_access.return_value = True

        meta = StorageObjectMeta(
            tenant_id="tenant-B",
            storage_key="key",
            checksum="abc",
            mime_type=None,
            size_bytes=10,
        )
        mock_adapter.put_object.return_value = meta

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        result = service.upload_file(
            tenant_id="tenant-A",
            data_category="raw",
            filename="data.csv",
            data=b"test",
        )
        assert result == meta


class TestStorageServiceDownload:
    def test_download_delegates_to_adapter(self):
        mock_adapter = MagicMock()
        mock_adapter.get_object.return_value = b"file content"
        mock_guard = MagicMock()
        mock_guard.check_read_access.return_value = True

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        result = service.download_file(tenant_id="tenant-A", key="tenants/tenant-A/raw/file.csv")

        assert result == b"file content"
        mock_adapter.get_object.assert_called_once_with(key="tenants/tenant-A/raw/file.csv", tenant_id="tenant-A")

    def test_download_denied_wrong_tenant(self):
        mock_adapter = MagicMock()
        mock_guard = MagicMock()
        mock_guard.check_read_access.side_effect = StorageAccessError("key", "wrong tenant")

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        with pytest.raises(StorageAccessError):
            service.download_file(tenant_id="tenant-A", key="tenants/tenant-B/raw/file.csv")


class TestStorageServiceDelete:
    def test_delete_validates_access_then_deletes(self):
        mock_adapter = MagicMock()
        mock_guard = MagicMock()
        mock_guard.check_delete_access.return_value = True

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        service.delete_file(tenant_id="tenant-A", key="tenants/tenant-A/raw/file.csv")

        mock_guard.check_delete_access.assert_called_once()
        mock_adapter.delete_object.assert_called_once_with(key="tenants/tenant-A/raw/file.csv", tenant_id="tenant-A")

    def test_delete_denied_wrong_tenant(self):
        mock_adapter = MagicMock()
        mock_guard = MagicMock()
        mock_guard.check_delete_access.side_effect = StorageAccessError("key", "wrong tenant")

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        with pytest.raises(StorageAccessError):
            service.delete_file(tenant_id="tenant-A", key="tenants/tenant-B/raw/file.csv")


class TestStorageServiceList:
    def test_list_filters_by_tenant_prefix(self):
        mock_adapter = MagicMock()
        meta_a = StorageObjectMeta(
            tenant_id="tenant-A",
            storage_key="tenants/tenant-A/raw/a.csv",
            checksum="a",
            mime_type=None,
            size_bytes=1,
        )
        meta_b = StorageObjectMeta(
            tenant_id="tenant-A",
            storage_key="tenants/tenant-A/clean/b.csv",
            checksum="b",
            mime_type=None,
            size_bytes=1,
        )
        mock_adapter.list_objects.return_value = [meta_a, meta_b]
        mock_guard = MagicMock()
        mock_guard.check_read_access.return_value = True

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        results = service.list_tenant_files(tenant_id="tenant-A")

        assert len(results) == 2
        mock_adapter.list_objects.assert_called_once()
        call_arg = mock_adapter.list_objects.call_args.kwargs["prefix"]
        assert call_arg.startswith("tenants/tenant-A/")

    def test_list_with_category_filter(self):
        mock_adapter = MagicMock()
        mock_adapter.list_objects.return_value = []
        mock_guard = MagicMock()
        mock_guard.check_read_access.return_value = True

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        service.list_tenant_files(tenant_id="tenant-A", data_category="raw")

        call_arg = mock_adapter.list_objects.call_args.kwargs["prefix"]
        assert "/raw/" in call_arg

    def test_list_with_explicit_prefix(self):
        mock_adapter = MagicMock()
        mock_adapter.list_objects.return_value = []
        mock_guard = MagicMock()
        mock_guard.check_read_access.return_value = True

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        service.list_tenant_files(tenant_id="tenant-A", prefix="tenants/tenant-A/custom/")

        call_arg = mock_adapter.list_objects.call_args.kwargs["prefix"]
        assert call_arg == "tenants/tenant-A/custom/"


class TestStorageServiceLifecycle:
    def test_archive_object_sets_state(self):
        mock_adapter = MagicMock()
        mock_guard = MagicMock()
        mock_guard.check_write_access.return_value = True

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        service.archive_object(tenant_id="tenant-A", key="tenants/tenant-A/raw/file.csv")

        mock_adapter.set_lifecycle_state.assert_called_once_with(
            "tenants/tenant-A/raw/file.csv", "archived", tenant_id="tenant-A"
        )

    def test_expire_object_sets_both_states(self):
        mock_adapter = MagicMock()
        mock_guard = MagicMock()
        mock_guard.check_write_access.return_value = True

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        service.expire_object(tenant_id="tenant-A", key="tenants/tenant-A/raw/file.csv")

        mock_adapter.set_lifecycle_state.assert_called_once_with(
            "tenants/tenant-A/raw/file.csv", "expired", tenant_id="tenant-A"
        )
        mock_adapter.set_retention_state.assert_called_once_with(
            "tenants/tenant-A/raw/file.csv", "deletable", tenant_id="tenant-A"
        )


class TestStorageServiceCleanup:
    def test_cleanup_deletes_only_expired_objects(self):
        mock_adapter = MagicMock()
        mock_guard = MagicMock()
        mock_guard.check_delete_access.return_value = True

        expired_meta = StorageObjectMeta(
            tenant_id="tenant-A",
            storage_key="tenants/tenant-A/raw/expired.csv",
            checksum="x",
            mime_type=None,
            size_bytes=1,
            lifecycle_state="expired",
        )
        active_meta = StorageObjectMeta(
            tenant_id="tenant-A",
            storage_key="tenants/tenant-A/raw/active.csv",
            checksum="y",
            mime_type=None,
            size_bytes=1,
            lifecycle_state="active",
        )
        mock_adapter.list_objects.return_value = [expired_meta, active_meta]

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        count = service.cleanup_expired(tenant_id="tenant-A")

        assert count == 1
        mock_adapter.delete_object.assert_called_once_with(key="tenants/tenant-A/raw/expired.csv", tenant_id="tenant-A")

    def test_cleanup_empty_returns_zero(self):
        mock_adapter = MagicMock()
        mock_adapter.list_objects.return_value = []
        mock_guard = MagicMock()

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        count = service.cleanup_expired(tenant_id="tenant-A")
        assert count == 0

    def test_cleanup_all_expired(self):
        mock_adapter = MagicMock()
        mock_guard = MagicMock()
        mock_guard.check_delete_access.return_value = True

        objs = [
            StorageObjectMeta(
                tenant_id="tenant-A",
                storage_key=f"tenants/tenant-A/raw/{i}.csv",
                checksum="x",
                mime_type=None,
                size_bytes=1,
                lifecycle_state="expired",
            )
            for i in range(3)
        ]
        mock_adapter.list_objects.return_value = objs

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        count = service.cleanup_expired(tenant_id="tenant-A")
        assert count == 3

    def test_archived_objects_not_deleted_during_cleanup(self):
        mock_adapter = MagicMock()
        mock_guard = MagicMock()
        mock_guard.check_delete_access.return_value = True

        objs = [
            StorageObjectMeta(
                tenant_id="tenant-A",
                storage_key="tenants/tenant-A/raw/archived.csv",
                checksum="x",
                mime_type=None,
                size_bytes=1,
                lifecycle_state="archived",
            ),
            StorageObjectMeta(
                tenant_id="tenant-A",
                storage_key="tenants/tenant-A/raw/active.csv",
                checksum="y",
                mime_type=None,
                size_bytes=1,
                lifecycle_state="active",
            ),
        ]
        mock_adapter.list_objects.return_value = objs

        service = StorageService(adapter=mock_adapter, guard=mock_guard)
        count = service.cleanup_expired(tenant_id="tenant-A")
        assert count == 0
        mock_adapter.delete_object.assert_not_called()
