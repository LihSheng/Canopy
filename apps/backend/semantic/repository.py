from sqlalchemy import desc
from sqlalchemy.orm import Session

from semantic.domain import EntityLink, ObjectType, PropertyMapping, SemanticMapping
from semantic.schema import ObjectTypeModel, SemanticMappingModel


class ObjectTypeRepository:
    def __init__(self, db: Session):
        self._db = db

    def save(self, domain: ObjectType) -> ObjectType:
        model = self._to_model(domain)
        merged = self._db.merge(model)
        self._db.commit()
        self._db.refresh(merged)
        return self._to_domain(merged)

    def get(self, id: str) -> ObjectType | None:
        model = self._db.query(ObjectTypeModel).filter(ObjectTypeModel.id == id).first()
        return self._to_domain(model) if model else None

    def get_by_key(self, tenant_id: str, key: str) -> ObjectType | None:
        model = (
            self._db.query(ObjectTypeModel)
            .filter(
                ObjectTypeModel.tenant_id == tenant_id,
                ObjectTypeModel.object_type_key == key,
            )
            .first()
        )
        return self._to_domain(model) if model else None

    def list_by_tenant(self, tenant_id: str) -> list[ObjectType]:
        models = (
            self._db.query(ObjectTypeModel)
            .filter(ObjectTypeModel.tenant_id == tenant_id)
            .order_by(ObjectTypeModel.created_at.desc())
            .all()
        )
        return [self._to_domain(m) for m in models]

    def delete(self, id: str) -> bool:
        model = self._db.query(ObjectTypeModel).filter(ObjectTypeModel.id == id).first()
        if model is None:
            return False
        self._db.delete(model)
        self._db.commit()
        return True

    def _to_model(self, d: ObjectType) -> ObjectTypeModel:
        return ObjectTypeModel(
            id=d.id,
            tenant_id=d.tenant_id,
            object_type_key=d.object_type_key,
            display_name=d.display_name,
            description=d.description,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )

    def _to_domain(self, m: ObjectTypeModel) -> ObjectType:
        return ObjectType(
            id=m.id,
            tenant_id=m.tenant_id,
            object_type_key=m.object_type_key,
            display_name=m.display_name,
            description=m.description,
            created_at=m.created_at,
            updated_at=m.updated_at,
        )


class SemanticMappingRepository:
    def __init__(self, db: Session):
        self._db = db

    def save(self, domain: SemanticMapping) -> SemanticMapping:
        model = self._to_model(domain)
        merged = self._db.merge(model)
        self._db.commit()
        self._db.refresh(merged)
        return self._to_domain(merged)

    def get(self, id: str) -> SemanticMapping | None:
        model = self._db.query(SemanticMappingModel).filter(SemanticMappingModel.id == id).first()
        return self._to_domain(model) if model else None

    def get_current(self, dataset_id: str, dataset_version_id: str) -> SemanticMapping | None:
        """Get the latest mapping version for a dataset version."""
        model = (
            self._db.query(SemanticMappingModel)
            .filter(
                SemanticMappingModel.dataset_id == dataset_id,
                SemanticMappingModel.dataset_version_id == dataset_version_id,
            )
            .order_by(desc(SemanticMappingModel.version_number))
            .first()
        )
        return self._to_domain(model) if model else None

    def get_max_version(self, dataset_id: str, dataset_version_id: str) -> int:
        result = (
            self._db.query(SemanticMappingModel.version_number)
            .filter(
                SemanticMappingModel.dataset_id == dataset_id,
                SemanticMappingModel.dataset_version_id == dataset_version_id,
            )
            .order_by(desc(SemanticMappingModel.version_number))
            .first()
        )
        return result[0] if result else 0

    def get_latest_by_object_type_id(self, tenant_id: str, object_type_id: str) -> SemanticMapping | None:
        """Get the latest mapping (highest version) for a given object_type_id within a tenant."""
        model = (
            self._db.query(SemanticMappingModel)
            .filter(
                SemanticMappingModel.tenant_id == tenant_id,
                SemanticMappingModel.object_type_id == object_type_id,
            )
            .order_by(desc(SemanticMappingModel.version_number))
            .first()
        )
        return self._to_domain(model) if model else None

    def list_by_dataset(self, dataset_id: str) -> list[SemanticMapping]:
        models = (
            self._db.query(SemanticMappingModel)
            .filter(SemanticMappingModel.dataset_id == dataset_id)
            .order_by(desc(SemanticMappingModel.version_number))
            .all()
        )
        return [self._to_domain(m) for m in models]

    def delete(self, id: str) -> bool:
        model = self._db.query(SemanticMappingModel).filter(SemanticMappingModel.id == id).first()
        if model is None:
            return False
        self._db.delete(model)
        self._db.commit()
        return True

    def _to_model(self, d: SemanticMapping) -> SemanticMappingModel:
        return SemanticMappingModel(
            id=d.id,
            tenant_id=d.tenant_id,
            dataset_id=d.dataset_id,
            dataset_version_id=d.dataset_version_id,
            version_number=d.version_number,
            object_type_id=d.object_type_id,
            object_type_key=d.object_type_key,
            properties=[
                {
                    "source_column": p.source_column,
                    "property_name": p.property_name,
                    "semantic_type": p.semantic_type,
                    "included": p.included,
                    "is_primary_key": p.is_primary_key,
                }
                for p in d.properties
            ],
            links=[
                {
                    "link_id": ln.link_id,
                    "display_name": ln.display_name,
                    "source_property_key": ln.source_property_key,
                    "target_object_type_id": ln.target_object_type_id,
                    "target_property_key": ln.target_property_key,
                    "cardinality": ln.cardinality,
                }
                for ln in (d.links or [])
            ],
            created_at=d.created_at,
            updated_at=d.updated_at,
        )

    def _to_domain(self, m: SemanticMappingModel) -> SemanticMapping | None:
        if m is None:
            return None
        return SemanticMapping(
            id=m.id,
            tenant_id=m.tenant_id,
            dataset_id=m.dataset_id,
            dataset_version_id=m.dataset_version_id,
            version_number=m.version_number,
            object_type_id=m.object_type_id,
            object_type_key=m.object_type_key,
            properties=[
                PropertyMapping(
                    source_column=p["source_column"],
                    property_name=p["property_name"],
                    semantic_type=p.get("semantic_type", "string"),
                    included=p.get("included", True),
                    is_primary_key=p.get("is_primary_key", False),
                )
                for p in (m.properties or [])
            ],
            links=[
                EntityLink(
                    link_id=ln["link_id"],
                    display_name=ln["display_name"],
                    source_property_key=ln["source_property_key"],
                    target_object_type_id=ln["target_object_type_id"],
                    target_property_key=ln["target_property_key"],
                    cardinality=ln.get("cardinality", "many_to_one"),
                )
                for ln in (m.links or [])
            ],
            created_at=m.created_at,
            updated_at=m.updated_at,
        )
