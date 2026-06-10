"""Entity materialization service — full snapshot replace materialization."""

import uuid
from collections.abc import Callable
from datetime import UTC, datetime

from common.errors import NotFoundError
from entity_formula_engine.engine import FormulaEngine
from entity_materialization.domain import EntityMaterializedRow
from entity_materialization.repository import EntityMaterializationRepository
from entity_revision.domain import EntityRevision
from entity_revision.repository import EntityRevisionRepository


class EntityMaterializationService:
    """Orchestrates materialization of published entity revisions.

    Reads source data via an injected source_data_reader, transforms rows
    using source bindings, and performs a full snapshot replace into the
    materialized rows store.
    """

    def __init__(
        self,
        revision_repo: EntityRevisionRepository,
        materialization_repo: EntityMaterializationRepository,
        source_data_reader: Callable[[dict], list[dict]],
    ):
        self._revision_repo = revision_repo
        self._materialization_repo = materialization_repo
        self._source_data_reader = source_data_reader

    # ── Materialization ──────────────────────────────────────────────────

    def materialize_entity(self, entity_id: str, revision_id: str) -> dict:
        """Run a full snapshot replace materialization for a published revision.

        Returns stats: { rows_inserted, rows_updated, rows_tombstoned }."""
        revision = self._revision_repo.get(revision_id)
        if revision is None or revision.entity_id != entity_id:
            raise NotFoundError("Entity or revision not found")

        # Build binding map: property_key -> source_field_name
        binding_map = self._build_binding_map(revision)
        if not binding_map:
            return {"rows_inserted": 0, "rows_updated": 0, "rows_tombstoned": 0}

        # Read source data (one active source node)
        source_rows = self._resolve_source_data(revision)

        # Transform source rows to entity rows
        primary_key_prop = self._find_primary_key(revision)
        new_rows: list[EntityMaterializedRow] = []
        new_row_ids: set[str] = set()

        for src_row in source_rows:
            row_id = self._determine_row_id(src_row, primary_key_prop, binding_map)
            row_data = self._transform_row(src_row, binding_map)
            # Evaluate computed properties
            for cp in revision.computed_properties or []:
                if not cp.is_active:
                    continue
                try:
                    result = FormulaEngine().evaluate(cp.formula, row_data)
                except Exception:
                    result = None
                row_data[cp.property_key] = result
            new_rows.append(
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=entity_id,
                    revision_id=revision_id,
                    row_id=row_id,
                    row_data=row_data,
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                )
            )
            new_row_ids.add(row_id)

        # Count existing rows before replace
        existing_rows = self._materialization_repo.get_rows(entity_id, revision_id, include_tombstones=False)
        if not existing_rows:
            # No existing rows for this revision yet. Seed from any other revision's
            # materialized rows so tombstone tracking works across revisions.
            other_rows = self._materialization_repo.get_rows_for_entity(entity_id, exclude_revision_id=revision_id)
            if other_rows:
                migrated = [
                    EntityMaterializedRow(
                        id=str(uuid.uuid4()),
                        entity_id=entity_id,
                        revision_id=revision_id,
                        row_id=r.row_id,
                        row_data=r.row_data,
                        is_tombstone=False,
                        materialized_at=datetime.now(UTC),
                    )
                    for r in other_rows
                ]
                self._materialization_repo.save_rows(entity_id, revision_id, migrated)
                existing_rows = migrated
        existing_row_ids = {r.row_id for r in existing_rows}

        rows_inserted = len(new_row_ids - existing_row_ids)
        rows_updated = len(new_row_ids & existing_row_ids)

        # Save all new rows (upsert)
        self._materialization_repo.save_rows(entity_id, revision_id, new_rows)

        # Tombstone rows that disappeared in this run
        rows_tombstoned = self._materialization_repo.tombstone_missing_rows(entity_id, revision_id, new_row_ids)

        return {
            "rows_inserted": rows_inserted,
            "rows_updated": rows_updated,
            "rows_tombstoned": rows_tombstoned,
        }

    # ── Read ───────────────────────────────────────────────────────────────

    def get_rows(
        self,
        entity_id: str,
        revision_id: str | None = None,
        include_tombstones: bool = False,
    ) -> list[EntityMaterializedRow]:
        """Return materialized rows for an entity.

        If revision_id is omitted, returns rows for the latest published revision."""
        if revision_id is None:
            revision = self._revision_repo.get_published(entity_id)
            if revision is None:
                return []
            revision_id = revision.id
        return self._materialization_repo.get_rows(entity_id, revision_id, include_tombstones)

    def get_row(self, entity_id: str, row_id: str) -> EntityMaterializedRow | None:
        """Return a single materialized row by entity_id + row_id."""
        return self._materialization_repo.get_row(entity_id, row_id)

    # ── Internal helpers ─────────────────────────────────────────────────

    def _build_binding_map(self, revision: EntityRevision) -> dict[str, str]:
        """Map property_key -> source_field_name from active bindings."""
        result: dict[str, str] = {}
        for binding in revision.source_bindings:
            result[binding.property_key] = binding.source_field_name
        return result

    def _resolve_source_data(self, revision: EntityRevision) -> list[dict]:
        """Read source rows from the active source node.

        Phase 8 uses one active source node per entity."""
        source_nodes = revision.source_nodes or []
        if not source_nodes:
            return []
        # Use the first source node as the active one
        active_node = source_nodes[0]
        return self._source_data_reader(active_node)

    def _transform_row(self, source_row: dict, binding_map: dict[str, str]) -> dict:
        """Map source fields to entity properties using bindings.

        Missing source fields produce null values."""
        return {
            property_key: source_row.get(source_field_name) for property_key, source_field_name in binding_map.items()
        }

    def _determine_row_id(self, source_row: dict, primary_key_prop: str | None, binding_map: dict[str, str]) -> str:
        """Create a deterministic row_id from the source row.

        Prefer the source field bound to the primary key property.
        Fall back to a content hash."""
        if primary_key_prop and primary_key_prop in binding_map:
            source_field = binding_map[primary_key_prop]
            if source_field in source_row:
                val = source_row[source_field]
                if val is not None:
                    return str(val)
        # Fallback: hash of the source row dict
        import hashlib
        import json

        canonical = json.dumps(source_row, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode()).hexdigest()

    def _find_primary_key(self, revision: EntityRevision) -> str | None:
        """Return the property_key of the primary key property, if any."""
        for prop in revision.properties:
            if prop.is_primary_key:
                return prop.property_key
        return None


# ── Source data reader (Phase 8 simplified adapter) ─────────────────────


def build_source_data_reader(db):
    """Build a source data reader callable for the given DB session.

    Resolves source_node.reference_id to a dataset version, reads all
    materialized rows from the dataset version's storage, and returns
    them as a list of dicts (column_name → value).

    Phase 8 uses a simplified read path. Tests can inject mock source
    rows by passing a custom callable instead of using this builder."""

    from dataset.repository import DatasetVersionRepository

    version_repo = DatasetVersionRepository(db)

    def _read(source_node: dict) -> list[dict]:
        reference_id = source_node.get("reference_id", "")
        if not reference_id:
            return []

        version = version_repo.get(reference_id)
        if version is None or not version.storage_path:
            return []

        rows: list[dict] = []
        try:
            with open(version.storage_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    import json

                    row = json.loads(line)
                    if isinstance(row, dict):
                        rows.append(row)
        except (FileNotFoundError, OSError):
            # Storage not available — return empty; caller handles gracefully
            return []

        return rows

    return _read
