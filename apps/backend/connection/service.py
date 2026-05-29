import uuid
from datetime import UTC, datetime

from common.errors import NotFoundError, ValidationError
from connection.domain import Connection, ConnectionStatus
from connection.repository import ConnectionRepository
from connection.secret_store import SecretStore, decrypt_secret_value
from control_plane.audit_service import AuditService


class ConnectionService:
    def __init__(
        self,
        repo: ConnectionRepository,
        audit: AuditService | None = None,
        secret_store: SecretStore | None = None,
    ):
        self._repo = repo
        self._audit = audit
        self._secret_store = secret_store

    def create_connection(
        self,
        project_id: str,
        source_type: str,
        name: str,
        config_json: dict | None = None,
    ) -> Connection:
        now = datetime.now(UTC)
        config = self._encrypt_config(config_json or {})
        connection = Connection(
            id=str(uuid.uuid4()),
            project_id=project_id,
            source_type=source_type,
            name=name,
            status=ConnectionStatus.ACTIVE.value,
            config_json=config,
            created_at=now,
        )
        return self._repo.save(connection)

    def get_connection(self, id: str) -> Connection | None:
        return self._repo.get(id)

    def list_connections(self, project_id: str) -> list[Connection]:
        return self._repo.list_by_project(project_id)

    def list_all_connections(self) -> list[Connection]:
        return self._repo.list_all()

    def create_static_file_connection(
        self,
        project_id: str,
        name: str,
        allowed_extensions: list[str] | None = None,
    ) -> Connection:
        config = {"allowed_extensions": allowed_extensions or [".csv", ".xlsx", ".json", ".parquet"]}
        return self.create_connection(project_id, "static_file", name, config)

    def update_connection_name(self, id: str, name: str) -> Connection:
        self._require_connection(id)
        updated = self._repo.update_name(id, name.strip())
        if updated is None:
            raise NotFoundError("Connection not found")
        return updated

    def pause_connection(self, id: str, actor_user_id: str) -> Connection:
        return self._transition(
            id=id,
            target_status=ConnectionStatus.PAUSED.value,
            allowed_statuses=[ConnectionStatus.ACTIVE.value, ConnectionStatus.ERROR.value],
            actor_user_id=actor_user_id,
            event_type="connection.paused",
        )

    def archive_connection(self, id: str, actor_user_id: str) -> Connection:
        return self._transition(
            id=id,
            target_status=ConnectionStatus.ARCHIVED.value,
            allowed_statuses=[
                ConnectionStatus.ACTIVE.value,
                ConnectionStatus.PAUSED.value,
                ConnectionStatus.ERROR.value,
            ],
            actor_user_id=actor_user_id,
            event_type="connection.archived",
        )

    def restore_connection(self, id: str, actor_user_id: str) -> Connection:
        return self._transition(
            id=id,
            target_status=ConnectionStatus.ACTIVE.value,
            allowed_statuses=[
                ConnectionStatus.PAUSED.value,
                ConnectionStatus.ARCHIVED.value,
                ConnectionStatus.SOFT_DELETED.value,
            ],
            actor_user_id=actor_user_id,
            event_type="connection.restored",
        )

    def soft_delete_connection(self, id: str, actor_user_id: str) -> Connection:
        self._ensure_no_active_dependencies(id)
        return self._transition(
            id=id,
            target_status=ConnectionStatus.SOFT_DELETED.value,
            allowed_statuses=[
                ConnectionStatus.ACTIVE.value,
                ConnectionStatus.PAUSED.value,
                ConnectionStatus.ARCHIVED.value,
                ConnectionStatus.ERROR.value,
                ConnectionStatus.INACTIVE.value,
            ],
            actor_user_id=actor_user_id,
            event_type="connection.soft_deleted",
        )

    def permanently_delete_connection(self, id: str, actor_user_id: str) -> dict:
        connection = self._require_connection(id)
        self._ensure_no_active_dependencies(id)
        deleted = self._repo.delete(id)
        if not deleted:
            raise NotFoundError("Connection not found")

        self._record_event(
            connection=connection,
            actor_user_id=actor_user_id,
            event_type="connection.permanently_deleted",
        )
        return {"deleted": True, "id": id}

    def get_dependency_summary(self, id: str) -> dict:
        self._require_connection(id)
        active_datasets = self._repo.count_active_datasets(id)
        active_runs = self._repo.count_active_runs(id)
        return {
            "connection_id": id,
            "active_dataset_count": active_datasets,
            "active_run_count": active_runs,
            "can_delete": active_datasets == 0 and active_runs == 0,
        }

    def _transition(
        self,
        id: str,
        target_status: str,
        allowed_statuses: list[str],
        actor_user_id: str,
        event_type: str,
    ) -> Connection:
        connection = self._require_connection(id)
        if connection.status not in allowed_statuses:
            raise ValidationError(f"Cannot move connection from '{connection.status}' to '{target_status}'")

        updated = self._repo.update_status(id, target_status)
        if updated is None:
            raise NotFoundError("Connection not found")

        self._record_event(connection=updated, actor_user_id=actor_user_id, event_type=event_type)
        return updated

    def _require_connection(self, id: str) -> Connection:
        connection = self._repo.get(id)
        if connection is None:
            raise NotFoundError("Connection not found")
        return connection

    def _ensure_no_active_dependencies(self, id: str) -> None:
        active_datasets = self._repo.count_active_datasets(id)
        active_runs = self._repo.count_active_runs(id)
        if active_datasets > 0 or active_runs > 0:
            raise ValidationError(
                "Connection has active dependencies: "
                f"{active_datasets} active dataset(s), {active_runs} queued/running run(s)"
            )

    def _encrypt_config(self, config_json: dict) -> dict:
        result = dict(config_json)
        password = result.get("password")
        if password and isinstance(password, str):
            store = self._secret_store or self._build_default_store()
            result["password"] = store.encrypt(password)
        return result

    def _decrypt_config(self, connection: Connection) -> dict:
        config = dict(connection.config_json or {})
        password = config.get("password")
        if password and isinstance(password, str):
            store = self._secret_store or self._build_default_store()
            config["password"] = decrypt_secret_value(password, store, allow_legacy_plaintext=True)
        return config

    @staticmethod
    def _build_default_store() -> SecretStore:
        from connection.secret_store import AesGcmSecretStore

        return AesGcmSecretStore()

    async def test_connection(self, id: str) -> dict:
        connection = self._require_connection(id)
        config = self._decrypt_config(connection)

        from connection.database_adapter import get_adapter

        adapter = get_adapter(connection.source_type)
        result = await adapter.test_connection(config)

        if result.get("success"):
            self._repo.update_config(
                id,
                {
                    "supports_cdc": result.get("supports_cdc", False),
                    "cdc_parameters": result.get("cdc_parameters", {}),
                },
            )
        return result

    async def discover_tables(self, id: str) -> list[dict]:
        connection = self._require_connection(id)
        config = self._decrypt_config(connection)

        from connection.cursor_detection import detect_cursor_column
        from connection.database_adapter import get_adapter

        adapter = get_adapter(connection.source_type)
        tables = await adapter.discover_tables(config)

        for table in tables:
            table["detected_cursor_column"] = detect_cursor_column(table.get("columns", []))

        # Check schema drift for each discovered table
        if connection.source_type in {"postgresql", "mysql"}:
            try:
                from schema_drift.service import SchemaDriftService

                drift_service = SchemaDriftService(self._repo._db)
                for table in tables:
                    raw_columns = table.get("columns", [])
                    drift_result = drift_service.check_and_record_drift(
                        connection_id=connection.id,
                        source_object_name=table["table_name"],
                        raw_columns=raw_columns,
                        detected_by="discovery",
                    )
                    if drift_result["drift_detected"]:
                        table["schema_drift"] = {
                            "drift_detected": True,
                            "is_breaking": drift_result["is_breaking"],
                        }
            except Exception:
                # Drift detection is advisory during discovery; never break discovery
                logger = __import__("logging").getLogger(__name__)
                logger.exception("Schema drift check failed during discovery")

        return tables

    async def preview_table(self, id: str, table: str) -> dict:
        connection = self._require_connection(id)
        config = self._decrypt_config(connection)

        from connection.cursor_detection import detect_cursor_column
        from connection.database_adapter import get_adapter

        adapter = get_adapter(connection.source_type)
        preview = await adapter.preview_table(config, table)

        cursor = detect_cursor_column(preview.get("columns", []))
        preview["detected_cursor_column"] = cursor
        return preview

    def _record_event(self, connection: Connection, actor_user_id: str, event_type: str) -> None:
        if self._audit is None:
            return

        self._audit.record_event(
            tenant_id=None,
            actor_user_id=actor_user_id,
            event_type=event_type,
            payload={
                "connection_id": connection.id,
                "project_id": connection.project_id,
                "source_type": connection.source_type,
                "status": connection.status,
            },
        )
