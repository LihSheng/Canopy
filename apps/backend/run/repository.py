from sqlalchemy.orm import Session

from run.domain import Run
from run.schema import RunModel


class RunRepository:
    def __init__(self, db: Session):
        self._db = db

    def save(self, domain: Run) -> Run:
        model = self._to_model(domain)
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def update(self, domain: Run) -> Run:
        model = self._db.query(RunModel).filter(RunModel.id == domain.id).first()
        if model is None:
            raise ValueError(f"Run {domain.id} not found")
        for key, value in domain.__dataclass_fields__.items():
            setattr(model, key, getattr(domain, key))
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def get(self, id: str, tenant_id: str | None = None) -> Run | None:
        q = self._db.query(RunModel).filter(RunModel.id == id)
        if tenant_id is not None:
            q = q.filter(RunModel.tenant_id == tenant_id)
        model = q.first()
        return self._to_domain(model) if model else None

    def list_all(self, tenant_id: str | None = None) -> list[Run]:
        q = self._db.query(RunModel)
        if tenant_id is not None:
            q = q.filter(RunModel.tenant_id == tenant_id)
        models = q.order_by(RunModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def list_by_tenant(self, tenant_id: str) -> list[Run]:
        return self.list_all(tenant_id=tenant_id)

    def list_by_dataset(self, dataset_id: str, tenant_id: str | None = None) -> list[Run]:
        q = self._db.query(RunModel).filter(RunModel.dataset_id == dataset_id)
        if tenant_id is not None:
            q = q.filter(RunModel.tenant_id == tenant_id)
        models = q.order_by(RunModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def list_by_project(self, project_id: str, tenant_id: str | None = None) -> list[Run]:
        q = self._db.query(RunModel).filter(RunModel.project_id == project_id)
        if tenant_id is not None:
            q = q.filter(RunModel.tenant_id == tenant_id)
        models = q.order_by(RunModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def get_latest_by_dataset(self, dataset_id: str, tenant_id: str | None = None) -> Run | None:
        q = self._db.query(RunModel).filter(RunModel.dataset_id == dataset_id)
        if tenant_id is not None:
            q = q.filter(RunModel.tenant_id == tenant_id)
        model = q.order_by(RunModel.created_at.desc()).first()
        return self._to_domain(model) if model else None

    def count_active_by_dataset(self, dataset_id: str, tenant_id: str | None = None) -> int:
        q = (
            self._db.query(RunModel)
            .filter(RunModel.dataset_id == dataset_id)
            .filter(RunModel.status.in_(["queued", "running"]))
        )
        if tenant_id is not None:
            q = q.filter(RunModel.tenant_id == tenant_id)
        return q.count()

    def _to_model(self, d: Run) -> RunModel:
        return RunModel(**{k: getattr(d, k) for k in d.__dataclass_fields__})

    def _to_domain(self, m: RunModel) -> Run:
        return Run(**{c.name: getattr(m, c.name) for c in m.__table__.columns})
