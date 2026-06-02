from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from connection.domain import Connection
from connection.schema import ConnectionModel
from dataset.schema import DatasetModel
from run.schema import RunModel


class ConnectionRepository:
    def __init__(self, db: Session):
        self._db = db

    def save(self, domain: Connection) -> Connection:
        model = self._to_model(domain)
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def get(self, id: str, tenant_id: str | None = None) -> Connection | None:
        q = self._db.query(ConnectionModel).filter(ConnectionModel.id == id)
        if tenant_id is not None:
            q = q.filter(ConnectionModel.tenant_id == tenant_id)
        model = q.first()
        return self._to_domain(model) if model else None

    def list_all(self, tenant_id: str | None = None) -> list[Connection]:
        q = (
            self._db.query(ConnectionModel)
            .filter(ConnectionModel.status != "soft_deleted")
            .filter(ConnectionModel.status != "deleted")
        )
        if tenant_id is not None:
            q = q.filter(ConnectionModel.tenant_id == tenant_id)
        models = q.order_by(ConnectionModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def list_by_tenant(self, tenant_id: str) -> list[Connection]:
        return self.list_all(tenant_id=tenant_id)

    def list_by_project(self, project_id: str, tenant_id: str | None = None) -> list[Connection]:
        q = (
            self._db.query(ConnectionModel)
            .filter(ConnectionModel.project_id == project_id)
            .filter(ConnectionModel.status != "soft_deleted")
            .filter(ConnectionModel.status != "deleted")
        )
        if tenant_id is not None:
            q = q.filter(ConnectionModel.tenant_id == tenant_id)
        models = q.order_by(ConnectionModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def update_status(self, id: str, status: str) -> Connection | None:
        model = self._db.query(ConnectionModel).filter(ConnectionModel.id == id).first()
        if model is None:
            return None
        model.status = status
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def update_name(self, id: str, name: str) -> Connection | None:
        model = self._db.query(ConnectionModel).filter(ConnectionModel.id == id).first()
        if model is None:
            return None
        model.name = name
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def update_config(self, id: str, config_json: dict) -> Connection | None:
        model = self._db.query(ConnectionModel).filter(ConnectionModel.id == id).first()
        if model is None:
            return None
        # Merge dict to preserve other configurations
        current_config = dict(model.config_json or {})
        current_config.update(config_json)
        model.config_json = current_config
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def count_active_datasets(self, connection_id: str) -> int:
        return (
            self._db.query(DatasetModel)
            .filter(DatasetModel.connection_id == connection_id)
            .filter(DatasetModel.status == "active")
            .count()
        )

    def count_active_runs(self, connection_id: str) -> int:
        return (
            self._db.query(RunModel)
            .filter(RunModel.connection_id == connection_id)
            .filter(RunModel.status.in_(["queued", "running"]))
            .count()
        )

    def resolve_static_source_file_path(self, connection: Connection) -> str:
        source_file_path = connection.config_json.get("source_file_path")
        if isinstance(source_file_path, str) and source_file_path:
            return source_file_path

        upload_id = connection.config_json.get("upload_id")
        if not isinstance(upload_id, str) or not upload_id:
            return ""

        try:
            return (
                self._db.execute(
                    text("select storage_path from uploads where id = :upload_id"),
                    {"upload_id": upload_id},
                ).scalar_one_or_none()
                or ""
            )
        except SQLAlchemyError:
            return ""

    def delete(self, id: str) -> bool:
        model = self._db.query(ConnectionModel).filter(ConnectionModel.id == id).first()
        if model is None:
            return False
        self._db.delete(model)
        self._db.commit()
        return True

    def _to_model(self, d: Connection) -> ConnectionModel:
        # Only persist columns that exist in the current control-plane schema.
        payload = {
            key: getattr(d, key) for key in ConnectionModel.__table__.columns.keys() if getattr(d, key) is not None
        }
        return ConnectionModel(**payload)

    def _to_domain(self, m: ConnectionModel) -> Connection:
        return Connection(**{c.name: getattr(m, c.name) for c in m.__table__.columns})
