"""Entity materialization repository — data access for entity_materialized_rows."""

from datetime import UTC, datetime

from sqlalchemy.orm import Session

from entity_materialization.domain import EntityMaterializedRow
from entity_materialization.schema import EntityMaterializedRowModel


class EntityMaterializationRepository:
    def __init__(self, db: Session):
        self._db = db

    # ── Write ──

    def save_rows(
        self,
        entity_id: str,
        revision_id: str,
        rows: list[EntityMaterializedRow],
    ) -> None:
        """Upsert rows for a given entity + revision.

        Existing rows with the same row_id are replaced (deleted then re-inserted
        to keep the logic simple and deterministic)."""
        if not rows:
            return

        row_ids = [r.row_id for r in rows]
        # Remove existing rows for this entity/revision that match incoming row_ids
        self._db.query(EntityMaterializedRowModel).filter(
            EntityMaterializedRowModel.entity_id == entity_id,
            EntityMaterializedRowModel.revision_id == revision_id,
            EntityMaterializedRowModel.row_id.in_(row_ids),
        ).delete(synchronize_session=False)

        for row in rows:
            self._db.add(
                EntityMaterializedRowModel(
                    id=row.id,
                    entity_id=row.entity_id,
                    revision_id=row.revision_id,
                    row_id=row.row_id,
                    row_data=row.row_data,
                    is_tombstone=row.is_tombstone,
                    materialized_at=row.materialized_at,
                    deleted_at=row.deleted_at,
                )
            )
        self._db.commit()

    def tombstone_missing_rows(
        self,
        entity_id: str,
        revision_id: str,
        new_row_ids: set[str],
    ) -> int:
        """Mark rows in this entity+revision that are NOT in new_row_ids as tombstones.

        Returns the count of rows tombstoned."""
        now = datetime.now(UTC)
        rows_to_tombstone = (
            self._db.query(EntityMaterializedRowModel)
            .filter(
                EntityMaterializedRowModel.entity_id == entity_id,
                EntityMaterializedRowModel.revision_id == revision_id,
                EntityMaterializedRowModel.row_id.notin_(list(new_row_ids)),
                EntityMaterializedRowModel.is_tombstone.is_(False),
            )
            .all()
        )
        count = len(rows_to_tombstone)
        for row in rows_to_tombstone:
            row.is_tombstone = True
            row.deleted_at = now
        self._db.commit()
        return count

    # ── Read ──

    def get_rows(
        self,
        entity_id: str,
        revision_id: str | None = None,
        include_tombstones: bool = False,
    ) -> list[EntityMaterializedRow]:
        """Return materialized rows for an entity.

        If revision_id is provided, filter to that revision.
        By default, tombstones are excluded."""
        q = self._db.query(EntityMaterializedRowModel).filter(
            EntityMaterializedRowModel.entity_id == entity_id,
        )
        if revision_id is not None:
            q = q.filter(EntityMaterializedRowModel.revision_id == revision_id)
        if not include_tombstones:
            q = q.filter(EntityMaterializedRowModel.is_tombstone.is_(False))
        models = q.order_by(EntityMaterializedRowModel.row_id).all()
        return [self._to_domain(m) for m in models]

    def get_rows_for_entity(
        self,
        entity_id: str,
        exclude_revision_id: str | None = None,
    ) -> list[EntityMaterializedRow]:
        """Return materialized rows for an entity across all revisions, excluding a specific revision."""
        q = self._db.query(EntityMaterializedRowModel).filter(
            EntityMaterializedRowModel.entity_id == entity_id,
            EntityMaterializedRowModel.is_tombstone.is_(False),
        )
        if exclude_revision_id is not None:
            q = q.filter(EntityMaterializedRowModel.revision_id != exclude_revision_id)
        models = q.order_by(EntityMaterializedRowModel.row_id).all()
        return [self._to_domain(m) for m in models]

    def get_row(self, entity_id: str, row_id: str) -> EntityMaterializedRow | None:
        """Return a single row by entity_id + row_id (any revision)."""
        model = (
            self._db.query(EntityMaterializedRowModel)
            .filter(
                EntityMaterializedRowModel.entity_id == entity_id,
                EntityMaterializedRowModel.row_id == row_id,
            )
            .first()
        )
        return self._to_domain(model) if model else None

    # ── Mapper ──

    def _to_domain(self, m: EntityMaterializedRowModel) -> EntityMaterializedRow:
        return EntityMaterializedRow(
            id=m.id,
            entity_id=m.entity_id,
            revision_id=m.revision_id,
            row_id=m.row_id,
            row_data=m.row_data,
            is_tombstone=m.is_tombstone,
            materialized_at=m.materialized_at,
            deleted_at=m.deleted_at,
        )
