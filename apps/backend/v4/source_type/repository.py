from sqlalchemy.orm import Session

from v4.source_type.domain import SourceType
from v4.source_type.schema import SourceTypeModel


class SourceTypeRepository:
    def __init__(self, db: Session):
        self._db = db

    def save(self, domain: SourceType) -> SourceType:
        model = self._to_model(domain)
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def list_all(self) -> list[SourceType]:
        models = self._db.query(SourceTypeModel).order_by(SourceTypeModel.key).all()
        return [self._to_domain(m) for m in models]

    def get_by_key(self, key: str) -> SourceType | None:
        model = self._db.query(SourceTypeModel).filter(SourceTypeModel.key == key).first()
        return self._to_domain(model) if model else None

    def get_enabled(self) -> list[SourceType]:
        models = self._db.query(SourceTypeModel).filter(SourceTypeModel.enabled == True).all()
        return [self._to_domain(m) for m in models]

    def _to_model(self, d: SourceType) -> SourceTypeModel:
        return SourceTypeModel(**{k: getattr(d, k) for k in d.__dataclass_fields__})

    def _to_domain(self, m: SourceTypeModel) -> SourceType:
        return SourceType(**{c.name: getattr(m, c.name) for c in m.__table__.columns})
