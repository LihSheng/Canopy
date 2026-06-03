import pytest

from connection.domain import Connection
from connection.secret_store import AesGcmSecretStore
from dataset.domain import Dataset, DatasetVersion
from semantic.schema_service import DatasetSchemaService


class _StubRepo:
    def __init__(self, obj):
        self._obj = obj

    def get(self, _id):
        return self._obj


class _PasswordCheckingAdapter:
    def __init__(self):
        self.received_password = None

    async def discover_tables(self, config: dict) -> list[dict]:
        self.received_password = config.get("password")
        if self.received_password != "secret123":
            raise AssertionError("schema introspection received encrypted password")
        return [
            {
                "table_name": "lv_emp_leave_request_file",
                "columns": [
                    {"name": "id", "data_type": "int"},
                    {"name": "created_at", "data_type": "timestamp"},
                ],
            }
        ]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_schema_decrypts_connection_password_before_db_introspection(monkeypatch):
    key = b"0123456789abcdef0123456789abcdef"
    monkeypatch.setenv("SECRET_KEY", key.decode("ascii"))

    dataset = Dataset(
        id="dataset-1",
        connection_id="connection-1",
        name="Leave Request File",
        source_object_name="lv_emp_leave_request_file",
    )
    version = DatasetVersion(
        id="version-1",
        dataset_id=dataset.id,
        status="ready",
        storage_path="",
    )
    connection = Connection(
        id=dataset.connection_id,
        source_type="mysql",
        name="HerdHR",
        config_json={
            "host": "127.0.0.1",
            "port": 33061,
            "database": "tenant_demo",
            "username": "homestead",
            "password": AesGcmSecretStore(key=key).encrypt("secret123"),
        },
    )
    adapter = _PasswordCheckingAdapter()

    service = DatasetSchemaService(db=None)
    service._dataset_repo = _StubRepo(dataset)
    service._version_repo = _StubRepo(version)
    service._connection_repo = _StubRepo(connection)
    monkeypatch.setattr("semantic.schema_service.get_adapter", lambda source_type: adapter)

    schema = await service.get_schema(dataset.id, version.id)

    assert adapter.received_password == "secret123"
    assert [column.column_name for column in schema] == ["id", "created_at"]
    assert [column.primitive_type for column in schema] == ["integer", "datetime"]
