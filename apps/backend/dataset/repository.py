from sqlalchemy.orm import Session

from dataset.domain import Dataset, DatasetVersion
from dataset.schema import DatasetModel, DatasetVersionModel


class DatasetRepository:
    def __init__(self, db: Session):
        self._db = db

    def save(self, domain: Dataset) -> Dataset:
        model = self._to_model(domain)
        merged = self._db.merge(model)
        self._db.commit()
        self._db.refresh(merged)
        return self._to_domain(merged)

    def get(self, id: str) -> Dataset | None:
        model = self._db.query(DatasetModel).filter(DatasetModel.id == id).first()
        return self._to_domain(model) if model else None

    def list_all(self) -> list[Dataset]:
        models = self._db.query(DatasetModel).order_by(DatasetModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def list_by_project(self, project_id: str) -> list[Dataset]:
        models = self._db.query(DatasetModel).filter(DatasetModel.project_id == project_id).order_by(DatasetModel.created_at.desc()).all()
        return [self._to_domain(m) for m in models]

    def update_active_version(self, dataset_id: str, version_id: str) -> Dataset | None:
        model = self._db.query(DatasetModel).filter(DatasetModel.id == dataset_id).first()
        if model is None:
            return None
        model.active_version_id = version_id
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def delete(self, id: str) -> bool:
        model = self._db.query(DatasetModel).filter(DatasetModel.id == id).first()
        if model is None:
            return False
        self._db.delete(model)
        self._db.commit()
        return True

    def _to_model(self, d: Dataset) -> DatasetModel:
        return DatasetModel(**{k: getattr(d, k) for k in d.__dataclass_fields__})

    def _to_domain(self, m: DatasetModel) -> Dataset:
        return Dataset(**{c.name: getattr(m, c.name) for c in m.__table__.columns})


class DatasetVersionRepository:
    def __init__(self, db: Session):
        self._db = db

    def save(self, domain: DatasetVersion) -> DatasetVersion:
        model = self._to_model(domain)
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return self._to_domain(model)

    def update(self, domain: DatasetVersion) -> DatasetVersion:
        model = self._to_model(domain)
        merged = self._db.merge(model)
        self._db.commit()
        self._db.refresh(merged)
        return self._to_domain(merged)

    def get(self, id: str) -> DatasetVersion | None:
        model = self._db.query(DatasetVersionModel).filter(DatasetVersionModel.id == id).first()
        return self._to_domain(model) if model else None

    def list_by_dataset(self, dataset_id: str) -> list[DatasetVersion]:
        models = self._db.query(DatasetVersionModel).filter(DatasetVersionModel.dataset_id == dataset_id).order_by(DatasetVersionModel.version_number.desc()).all()
        return [self._to_domain(m) for m in models]

    def get_active_version(self, dataset_id: str, active_version_id: str) -> DatasetVersion | None:
        model = self._db.query(DatasetVersionModel).filter(DatasetVersionModel.id == active_version_id, DatasetVersionModel.dataset_id == dataset_id).first()
        return self._to_domain(model) if model else None

    def get_latest_by_dataset(self, dataset_id: str) -> DatasetVersion | None:
        model = self._db.query(DatasetVersionModel).filter(DatasetVersionModel.dataset_id == dataset_id).order_by(DatasetVersionModel.version_number.desc()).first()
        return self._to_domain(model) if model else None

    def count_by_dataset(self, dataset_id: str) -> int:
        return self._db.query(DatasetVersionModel).filter(DatasetVersionModel.dataset_id == dataset_id).count()

    def delete(self, id: str) -> bool:
        model = self._db.query(DatasetVersionModel).filter(DatasetVersionModel.id == id).first()
        if model is None:
            return False
        self._db.delete(model)
        self._db.commit()
        return True

    def delete_by_dataset(self, dataset_id: str) -> int:
        deleted = (
            self._db.query(DatasetVersionModel)
            .filter(DatasetVersionModel.dataset_id == dataset_id)
            .delete(synchronize_session=False)
        )
        self._db.commit()
        return deleted

    def _to_model(self, d: DatasetVersion) -> DatasetVersionModel:
        return DatasetVersionModel(**{k: getattr(d, k) for k in d.__dataclass_fields__})

    def _to_domain(self, m: DatasetVersionModel) -> DatasetVersion:
        return DatasetVersion(**{c.name: getattr(m, c.name) for c in m.__table__.columns})

