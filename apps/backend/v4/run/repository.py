from sqlalchemy.orm import Session

from v4.run.domain import Run
from v4.run.schema import RunModel


class RunRepository:
    def __init__(self, db: Session):
        self._db = db

    def save(self, domain: Run) -> Run:
        model = self._to_model(domain)
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def get(self, id: str) -> Run | None:
        model = self._db.query(RunModel).filter(RunModel.id == id).first()
        return self._to_domain(model) if model else None

    def list_by_dataset(self, dataset_id: str) -> list[Run]:
        models = self._db.query(RunModel).filter(RunModel.dataset_id == dataset_id).order_by(RunModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def list_by_project(self, project_id: str) -> list[Run]:
        models = self._db.query(RunModel).filter(RunModel.project_id == project_id).order_by(RunModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def get_latest_by_dataset(self, dataset_id: str) -> Run | None:
        model = self._db.query(RunModel).filter(RunModel.dataset_id == dataset_id).order_by(RunModel.created_at.desc()).first()
        return self._to_domain(model) if model else None

    def _to_model(self, d: Run) -> RunModel:
        return RunModel(**{k: getattr(d, k) for k in d.__dataclass_fields__})

    def _to_domain(self, m: RunModel) -> Run:
        return Run(**{c.name: getattr(m, c.name) for c in m.__table__.columns})
