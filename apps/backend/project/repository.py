from sqlalchemy.orm import Session

from project.domain import Project
from project.schema import ProjectModel


class ProjectRepository:
    def __init__(self, db: Session):
        self._db = db

    def save(self, domain: Project) -> Project:
        model = self._to_model(domain)
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def get(self, id: str) -> Project | None:
        model = self._db.query(ProjectModel).filter(ProjectModel.id == id).first()
        return self._to_domain(model) if model else None

    def list_all(self) -> list[Project]:
        models = self._db.query(ProjectModel).order_by(ProjectModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def delete(self, id: str) -> bool:
        model = self._db.query(ProjectModel).filter(ProjectModel.id == id).first()
        if model is None:
            return False
        self._db.delete(model)
        self._db.commit()
        return True

    def _to_model(self, d: Project) -> ProjectModel:
        return ProjectModel(**{k: getattr(d, k) for k in d.__dataclass_fields__})

    def _to_domain(self, m: ProjectModel) -> Project:
        return Project(**{c.name: getattr(m, c.name) for c in m.__table__.columns})
