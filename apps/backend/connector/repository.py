"""Repository for the tenant-aware connector registry."""

from sqlalchemy.orm import Session

from connector.domain import ConnectorContract
from connector.schema import ConnectorRegistryModel


class ConnectorRegistryRepository:
    """Persistence for ConnectorContract in the connector_registry table.

    All queries support optional tenant_id filtering for tenant isolation.
    """

    def __init__(self, db: Session):
        self._db = db

    def save(self, domain: ConnectorContract) -> ConnectorContract:
        """Insert or update a connector in the registry."""
        model = self._to_model(domain)
        merged = self._db.merge(model)
        self._db.commit()
        self._db.refresh(merged)
        return self._to_domain(merged)

    def get(self, id: str, tenant_id: str | None = None) -> ConnectorContract | None:
        """Retrieve a connector by id, optionally scoped to a tenant."""
        q = self._db.query(ConnectorRegistryModel).filter(ConnectorRegistryModel.id == id)
        if tenant_id is not None:
            q = q.filter(ConnectorRegistryModel.tenant_id == tenant_id)
        model = q.first()
        return self._to_domain(model) if model else None

    def list_by_tenant(self, tenant_id: str) -> list[ConnectorContract]:
        """List all connectors for a given tenant."""
        models = (
            self._db.query(ConnectorRegistryModel)
            .filter(ConnectorRegistryModel.tenant_id == tenant_id)
            .order_by(ConnectorRegistryModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_by_type(self, tenant_id: str, type_: str) -> list[ConnectorContract]:
        """List connectors of a specific type for a tenant."""
        models = (
            self._db.query(ConnectorRegistryModel)
            .filter(ConnectorRegistryModel.tenant_id == tenant_id)
            .filter(ConnectorRegistryModel.type == type_)
            .order_by(ConnectorRegistryModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def list_all(self, tenant_id: str | None = None) -> list[ConnectorContract]:
        """List all connectors, optionally filtered by tenant."""
        q = self._db.query(ConnectorRegistryModel)
        if tenant_id is not None:
            q = q.filter(ConnectorRegistryModel.tenant_id == tenant_id)
        models = q.order_by(ConnectorRegistryModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def update_status(self, id: str, status: str) -> ConnectorContract | None:
        """Update the status of a connector."""
        model = self._db.query(ConnectorRegistryModel).filter(ConnectorRegistryModel.id == id).first()
        if model is None:
            return None
        model.status = status
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def update_metadata(self, id: str, metadata: dict) -> ConnectorContract | None:
        """Merge new metadata into a connector's existing metadata."""
        model = self._db.query(ConnectorRegistryModel).filter(ConnectorRegistryModel.id == id).first()
        if model is None:
            return None
        current = dict(model.metadata_json or {})
        current.update(metadata)
        model.metadata_json = current
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def delete(self, id: str) -> bool:
        """Hard-delete a connector from the registry."""
        model = self._db.query(ConnectorRegistryModel).filter(ConnectorRegistryModel.id == id).first()
        if model is None:
            return False
        self._db.delete(model)
        self._db.commit()
        return True

    @staticmethod
    def _to_model(d: ConnectorContract) -> ConnectorRegistryModel:
        payload = {
            key: getattr(d, key)
            for key in ConnectorRegistryModel.__table__.columns.keys()
            if getattr(d, key) is not None
        }
        return ConnectorRegistryModel(**payload)

    @staticmethod
    def _to_domain(m: ConnectorRegistryModel) -> ConnectorContract:
        return ConnectorContract(**{c.name: getattr(m, c.name) for c in m.__table__.columns})
