import uuid

from sqlalchemy.orm import Session

from feature_flags.domain import FeatureFlag
from feature_flags.schema import FeatureFlagModel


class FeatureFlagRepository:
    """Repository for global feature flags."""

    def __init__(self, db: Session):
        self._db = db

    def get_all(self) -> list[FeatureFlag]:
        models = self._db.query(FeatureFlagModel).order_by(FeatureFlagModel.flag_key).all()
        return [_to_domain(m) for m in models]

    def get_enabled(self) -> dict[str, bool]:
        """Return a map of flag_key -> enabled for all flags."""
        models = self._db.query(FeatureFlagModel).all()
        return {m.flag_key: m.enabled for m in models}

    def get_by_key(self, flag_key: str) -> FeatureFlag | None:
        model = self._db.query(FeatureFlagModel).filter(FeatureFlagModel.flag_key == flag_key).first()
        return _to_domain(model) if model else None

    def upsert(self, flag_key: str, description: str, enabled: bool) -> FeatureFlag:
        existing = self._db.query(FeatureFlagModel).filter(FeatureFlagModel.flag_key == flag_key).first()
        if existing:
            existing.description = description
            existing.enabled = enabled
            self._db.commit()
            self._db.refresh(existing)
            return _to_domain(existing)

        model = FeatureFlagModel(
            id=str(uuid.uuid4()),
            flag_key=flag_key,
            description=description,
            enabled=enabled,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return _to_domain(model)

    def set_enabled(self, flag_key: str, enabled: bool) -> FeatureFlag | None:
        model = self._db.query(FeatureFlagModel).filter(FeatureFlagModel.flag_key == flag_key).first()
        if not model:
            return None
        model.enabled = enabled
        self._db.commit()
        self._db.refresh(model)
        return _to_domain(model)

    def seed_defaults(self, defaults: list[dict]) -> None:
        """Ensure default flags exist without overwriting existing values."""
        for d in defaults:
            existing = self._db.query(FeatureFlagModel).filter(FeatureFlagModel.flag_key == d["flag_key"]).first()
            if existing:
                continue
            model = FeatureFlagModel(
                id=str(uuid.uuid4()),
                flag_key=d["flag_key"],
                description=d.get("description", ""),
                enabled=d.get("enabled", False),
            )
            self._db.add(model)
        self._db.commit()


def _to_domain(model: FeatureFlagModel) -> FeatureFlag:
    return FeatureFlag(
        id=model.id,
        flag_key=model.flag_key,
        description=model.description,
        enabled=model.enabled,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )
