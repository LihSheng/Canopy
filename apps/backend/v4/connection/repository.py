from sqlalchemy.orm import Session

from v4.connection.domain import Connection
from v4.connection.schema import ConnectionModel


class ConnectionRepository:
    def __init__(self, db: Session):
        self._db = db

    def save(self, domain: Connection) -> Connection:
        model = self._to_model(domain)
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def get(self, id: str) -> Connection | None:
        model = self._db.query(ConnectionModel).filter(ConnectionModel.id == id).first()
        return self._to_domain(model) if model else None

    def list_by_project(self, project_id: str) -> list[Connection]:
        models = self._db.query(ConnectionModel).filter(ConnectionModel.project_id == project_id).order_by(ConnectionModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def delete(self, id: str) -> bool:
        model = self._db.query(ConnectionModel).filter(ConnectionModel.id == id).first()
        if model is None:
            return False
        self._db.delete(model)
        self._db.commit()
        return True

    def _to_model(self, d: Connection) -> ConnectionModel:
        return ConnectionModel(**{k: getattr(d, k) for k in d.__dataclass_fields__})

    def _to_domain(self, m: ConnectionModel) -> Connection:
        return Connection(**{c.name: getattr(m, c.name) for c in m.__table__.columns})
