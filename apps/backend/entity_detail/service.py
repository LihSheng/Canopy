"""Entity detail service — builds enriched entity detail responses."""

from entity_detail.field_model import FieldGroup, FieldUnifier
from entity_formula_engine.engine import FormulaEngine
from entity_link_resolver.service import LinkResolverService
from entity_materialization.repository import EntityMaterializationRepository
from entity_revision.domain import EntityRevision
from entity_revision.repository import EntityRevisionRepository


class EntityDetailService:
    """Orchestrates entity detail enrichment with field groups, previews, and status."""

    def __init__(
        self,
        revision_repo: EntityRevisionRepository,
        materialization_repo: EntityMaterializationRepository,
        link_resolver: LinkResolverService,
        formula_engine: FormulaEngine,
    ):
        self._revision_repo = revision_repo
        self._materialization_repo = materialization_repo
        self._link_resolver = link_resolver
        self._formula_engine = formula_engine

    # ── Field groups ────────────────────────────────────────────────────

    def get_field_groups(self, revision: EntityRevision) -> list[FieldGroup]:
        """Return base and computed properties grouped and sorted."""
        return FieldGroup.group_fields(
            FieldUnifier.unify_fields(
                revision.properties or [],
                revision.computed_properties or [],
            )
        )

    # ── Materialized preview ────────────────────────────────────────────

    def get_entity_preview(self, entity_id: str, revision_id: str, limit: int = 5) -> list[dict]:
        """Return first *limit* materialized rows as plain dicts."""
        rows = self._materialization_repo.get_rows(
            entity_id=entity_id,
            revision_id=revision_id,
            include_tombstones=False,
        )
        return [
            {
                "id": r.id,
                "entity_id": r.entity_id,
                "revision_id": r.revision_id,
                "row_id": r.row_id,
                "row_data": r.row_data,
                "is_tombstone": r.is_tombstone,
                "materialized_at": r.materialized_at.isoformat() if r.materialized_at else None,
            }
            for r in rows[:limit]
        ]

    # ── Link status ─────────────────────────────────────────────────────

    def get_link_status(self, entity_id: str, revision: EntityRevision) -> list[dict]:
        """Return resolvable status for each link in the revision."""
        from entity_revision.domain import EntityLink

        status: list[dict] = []
        for raw_link in revision.links or []:
            if isinstance(raw_link, dict):
                link = EntityLink.from_dict(raw_link)
            else:
                link = raw_link
            target_published = self._revision_repo.get_published(link.target_entity_id)
            resolvable = target_published is not None
            status.append(
                {
                    "link_id": link.link_id,
                    "display_name": link.display_name,
                    "target_entity_id": link.target_entity_id,
                    "cardinality": link.cardinality,
                    "resolvable": resolvable,
                }
            )
        return status

    # ── Computed property warnings ────────────────────────────────────

    def get_computed_property_warnings(self, revision: EntityRevision) -> list[str]:
        """Return warnings for computed properties that reference missing properties."""
        property_keys = {p.property_key for p in revision.properties or []}
        warnings: list[str] = []
        for cp in revision.computed_properties or []:
            if not cp.is_active:
                continue
            try:
                refs = self._formula_engine.extract_property_references(cp.formula)
            except Exception:
                continue
            for ref in refs:
                if ref not in property_keys:
                    warnings.append(
                        f"Computed property '{cp.property_key}' references "
                        f"property '{ref}' which is missing or renamed."
                    )
        return warnings
