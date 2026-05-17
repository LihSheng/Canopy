import uuid
from datetime import UTC, datetime

from v4.connection.domain import Connection, ConnectionStatus
from v4.connection.repository import ConnectionRepository


class ConnectionService:
    def __init__(self, repo: ConnectionRepository):
        self._repo = repo

    def create_connection(self, project_id: str, source_type: str, name: str, config_json: dict | None = None) -> Connection:
        now = datetime.now(UTC)
        connection = Connection(
            id=str(uuid.uuid4()),
            project_id=project_id,
            source_type=source_type,
            name=name,
            status=ConnectionStatus.ACTIVE.value,
            config_json=config_json or {},
            created_at=now,
        )
        return self._repo.save(connection)

    def get_connection(self, id: str) -> Connection | None:
        return self._repo.get(id)

    def list_connections(self, project_id: str) -> list[Connection]:
        return self._repo.list_by_project(project_id)

    def create_static_file_connection(self, project_id: str, name: str, allowed_extensions: list[str] | None = None) -> Connection:
        config = {"allowed_extensions": allowed_extensions or [".csv", ".xlsx", ".json", ".parquet"]}
        return self.create_connection(project_id, "static_file", name, config)
