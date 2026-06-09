"""Entity revision repository — data access for entity_revisions and dependencies."""

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from entity_revision.domain import (
    ComputedProperty,
    EntityLink,
    EntityProperty,
    EntityRevision,
    EntityRevisionDependency,
    SourceBinding,
)
from entity_revision.schema import EntityRevisionDependencyModel, EntityRevisionModel


def _try_link_from_dict(lnk: dict) -> EntityLink | dict:
    try:
        return EntityLink.from_dict(lnk)
    except ValueError:
        return lnk


class EntityRevisionRepository:
    def __init__(self, db: Session):
        self._db = db

    # ── Create / update ──

    def save(self, domain: EntityRevision) -> EntityRevision:
        model = self._to_model(domain)
        merged = self._db.merge(model)
        self._db.commit()
        self._db.refresh(merged)
        return self._to_domain(merged)

    # ── Read ──

    def get(self, revision_id: str) -> EntityRevision | None:
        model = self._db.query(EntityRevisionModel).filter(EntityRevisionModel.id == revision_id).first()
        return self._to_domain(model) if model else None

    def get_by_entity_and_status(self, entity_id: str, status: str) -> EntityRevision | None:
        model = (
            self._db.query(EntityRevisionModel)
            .filter(
                EntityRevisionModel.entity_id == entity_id,
                EntityRevisionModel.status == status,
            )
            .first()
        )
        return self._to_domain(model) if model else None

    def get_published(self, entity_id: str) -> EntityRevision | None:
        return self.get_by_entity_and_status(entity_id, "published")

    def get_draft(self, entity_id: str) -> EntityRevision | None:
        return self.get_by_entity_and_status(entity_id, "draft")

    def list_by_entity(self, entity_id: str) -> list[EntityRevision]:
        models = (
            self._db.query(EntityRevisionModel)
            .filter(EntityRevisionModel.entity_id == entity_id)
            .order_by(desc(EntityRevisionModel.revision_number))
            .all()
        )
        return [self._to_domain(m) for m in models]

    def get_max_revision_number(self, entity_id: str) -> int:
        result = (
            self._db.query(func.max(EntityRevisionModel.revision_number))
            .filter(EntityRevisionModel.entity_id == entity_id)
            .scalar()
        )
        return result if result else 0

    def count_by_entity(self, entity_id: str) -> int:
        return (
            self._db.query(func.count(EntityRevisionModel.id))
            .filter(EntityRevisionModel.entity_id == entity_id)
            .scalar()
            or 0
        )

    # ── Dependency queries (for delete protection) ──

    def has_published_dependency_on_dataset(self, dataset_id: str) -> bool:
        """Check if any published revision depends on the given dataset."""
        count = (
            self._db.query(func.count(EntityRevisionDependencyModel.id))
            .join(
                EntityRevisionModel,
                EntityRevisionDependencyModel.revision_id == EntityRevisionModel.id,
            )
            .filter(
                EntityRevisionModel.status == "published",
                EntityRevisionDependencyModel.dependency_type == "dataset",
                EntityRevisionDependencyModel.dependency_id == dataset_id,
            )
            .scalar()
        )
        return count > 0 if count else False

    def has_published_dependency_on_dataset_version(self, version_id: str) -> bool:
        """Check if any published revision depends on the given dataset version."""
        count = (
            self._db.query(func.count(EntityRevisionDependencyModel.id))
            .join(
                EntityRevisionModel,
                EntityRevisionDependencyModel.revision_id == EntityRevisionModel.id,
            )
            .filter(
                EntityRevisionModel.status == "published",
                EntityRevisionDependencyModel.dependency_type == "dataset_version",
                EntityRevisionDependencyModel.dependency_id == version_id,
            )
            .scalar()
        )
        return count > 0 if count else False

    def count_published_entities_using_dataset(self, dataset_id: str) -> int:
        """Count distinct published entity revisions that depend on a dataset."""
        result = (
            self._db.query(func.count(func.distinct(EntityRevisionModel.entity_id)))
            .join(
                EntityRevisionDependencyModel,
                EntityRevisionDependencyModel.revision_id == EntityRevisionModel.id,
            )
            .filter(
                EntityRevisionModel.status == "published",
                EntityRevisionDependencyModel.dependency_type == "dataset",
                EntityRevisionDependencyModel.dependency_id == dataset_id,
            )
            .scalar()
        )
        return int(result or 0)

    # ── Delete ──

    def delete(self, revision_id: str) -> bool:
        model = self._db.query(EntityRevisionModel).filter(EntityRevisionModel.id == revision_id).first()
        if model is None:
            return False
        self._db.delete(model)
        self._db.commit()
        return True

    def delete_drafts_for_entity(self, entity_id: str) -> int:
        """Delete all draft revisions for an entity. Returns count deleted."""
        drafts = (
            self._db.query(EntityRevisionModel)
            .filter(
                EntityRevisionModel.entity_id == entity_id,
                EntityRevisionModel.status == "draft",
            )
            .all()
        )
        count = len(drafts)
        for d in drafts:
            self._db.delete(d)
        self._db.commit()
        return count

    # ── Dependencies ──

    def save_dependencies(self, revision_id: str, dependencies: list[EntityRevisionDependency]) -> None:
        """Replace all dependencies for a revision."""
        self._db.query(EntityRevisionDependencyModel).filter(
            EntityRevisionDependencyModel.revision_id == revision_id
        ).delete()
        for dep in dependencies:
            self._db.add(
                EntityRevisionDependencyModel(
                    id=dep.id,
                    revision_id=revision_id,
                    dependency_type=dep.dependency_type,
                    dependency_id=dep.dependency_id,
                )
            )
        self._db.commit()

    def get_dependencies(self, revision_id: str) -> list[EntityRevisionDependency]:
        models = (
            self._db.query(EntityRevisionDependencyModel)
            .filter(EntityRevisionDependencyModel.revision_id == revision_id)
            .all()
        )
        return [
            EntityRevisionDependency(
                id=m.id,
                revision_id=m.revision_id,
                dependency_type=m.dependency_type,
                dependency_id=m.dependency_id,
            )
            for m in models
        ]

    # ── Mappers ──

    def _to_model(self, d: EntityRevision) -> EntityRevisionModel:
        return EntityRevisionModel(
            id=d.id,
            entity_id=d.entity_id,
            revision_number=d.revision_number,
            status=d.status,
            forked_from_revision_id=d.forked_from_revision_id,
            properties=[
                {
                    "property_id": p.property_id,
                    "property_key": p.property_key,
                    "display_name": p.display_name,
                    "semantic_type": p.semantic_type,
                    "is_required": p.is_required,
                    "is_primary_key": p.is_primary_key,
                    "sort_order": p.sort_order,
                }
                for p in d.properties
            ],
            source_bindings=[
                {
                    "property_key": b.property_key,
                    "source_node_id": b.source_node_id,
                    "source_field_name": b.source_field_name,
                    "is_active": b.is_active,
                }
                for b in d.source_bindings
            ],
            planned_bindings=[
                {
                    "property_key": b.property_key,
                    "source_node_id": b.source_node_id,
                    "source_field_name": b.source_field_name,
                    "is_active": b.is_active,
                }
                for b in d.planned_bindings
            ],
            links=[lnk.to_dict() if isinstance(lnk, EntityLink) else lnk for lnk in (d.links or [])],
            source_nodes=d.source_nodes or [],
            computed_properties=[
                {
                    "id": cp.id,
                    "property_key": cp.property_key,
                    "display_name": cp.display_name,
                    "formula": cp.formula,
                    "formula_type": cp.formula_type,
                    "inputs": cp.inputs,
                    "output_type": cp.output_type,
                    "sort_order": cp.sort_order,
                    "is_active": cp.is_active,
                }
                for cp in d.computed_properties
            ],
            layout_state=d.layout_state or {},
            lock_holder_id=d.lock_holder_id,
            locked_at=d.locked_at,
            created_at=d.created_at,
            updated_at=d.updated_at,
            published_at=d.published_at,
        )

    def _to_domain(self, m: EntityRevisionModel) -> EntityRevision:
        return EntityRevision(
            id=m.id,
            entity_id=m.entity_id,
            revision_number=m.revision_number,
            status=m.status,
            forked_from_revision_id=m.forked_from_revision_id,
            properties=[
                EntityProperty(
                    property_id=p.get("property_id", ""),
                    property_key=p.get("property_key", ""),
                    display_name=p.get("display_name", ""),
                    semantic_type=p.get("semantic_type", "string"),
                    is_required=p.get("is_required", False),
                    is_primary_key=p.get("is_primary_key", False),
                    sort_order=p.get("sort_order", 0),
                )
                for p in (m.properties or [])
            ],
            source_bindings=[
                SourceBinding(
                    property_key=b.get("property_key", ""),
                    source_node_id=b.get("source_node_id", ""),
                    source_field_name=b.get("source_field_name", ""),
                    is_active=b.get("is_active", True),
                )
                for b in (m.source_bindings or [])
            ],
            planned_bindings=[
                SourceBinding(
                    property_key=b.get("property_key", ""),
                    source_node_id=b.get("source_node_id", ""),
                    source_field_name=b.get("source_field_name", ""),
                    is_active=b.get("is_active", True),
                )
                for b in (m.planned_bindings or [])
            ],
            links=[(_try_link_from_dict(lnk) if isinstance(lnk, dict) else lnk) for lnk in (m.links or [])],
            source_nodes=m.source_nodes or [],
            computed_properties=[
                ComputedProperty(
                    id=cp.get("id", ""),
                    property_key=cp.get("property_key", ""),
                    display_name=cp.get("display_name", ""),
                    formula=cp.get("formula", ""),
                    formula_type=cp.get("formula_type", "arithmetic"),
                    inputs=cp.get("inputs", []),
                    output_type=cp.get("output_type", "string"),
                    sort_order=cp.get("sort_order", 0),
                    is_active=cp.get("is_active", True),
                )
                for cp in (m.computed_properties or [])
            ],
            layout_state=m.layout_state or {},
            lock_holder_id=m.lock_holder_id,
            locked_at=m.locked_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
            published_at=m.published_at,
        )
