from sqlalchemy.orm import Session

from retention.domain import RetentionPolicy
from retention.schema import RetentionPolicyModel


class RetentionPolicyRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_dataset(self, dataset_id: str) -> RetentionPolicy | None:
        model = (
            self._db.query(RetentionPolicyModel)
            .filter(RetentionPolicyModel.dataset_id == dataset_id, RetentionPolicyModel.is_active.is_(True))
            .order_by(RetentionPolicyModel.created_at.desc())
            .first()
        )
        return self._to_domain(model) if model else None

    def save(self, domain: RetentionPolicy) -> RetentionPolicy:
        model = self._to_model(domain)
        merged = self._db.merge(model)
        self._db.commit()
        self._db.refresh(merged)
        return self._to_domain(merged)

    def _to_model(self, d: RetentionPolicy) -> RetentionPolicyModel:
        return RetentionPolicyModel(**{k: getattr(d, k) for k in d.__dataclass_fields__})

    def _to_domain(self, m: RetentionPolicyModel) -> RetentionPolicy:
        return RetentionPolicy(**{c.name: getattr(m, c.name) for c in m.__table__.columns})
