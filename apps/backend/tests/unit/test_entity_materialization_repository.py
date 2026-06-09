"""Unit tests for EntityMaterializationRepository — materialized row storage."""

import uuid
from datetime import UTC, datetime

import pytest

from entity_materialization.domain import EntityMaterializedRow
from entity_materialization.repository import EntityMaterializationRepository
from entity_revision.domain import EntityRevision, RevisionStatus
from entity_revision.repository import EntityRevisionRepository
from semantic.domain import ObjectType
from semantic.repository import ObjectTypeRepository

pytestmark = pytest.mark.unit


@pytest.fixture
def seed_entity(db_session):
    repo = ObjectTypeRepository(db_session)
    obj = ObjectType(
        id=str(uuid.uuid4()),
        tenant_id="test-tenant-1",
        object_type_key="mat_test_entity",
        display_name="Materialization Test Entity",
        description="Entity for materialization tests",
        created_at=datetime.now(UTC),
    )
    return repo.save(obj)


@pytest.fixture
def seed_published_revision(db_session, seed_entity):
    repo = EntityRevisionRepository(db_session)
    revision = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=seed_entity.id,
        revision_number=1,
        status=RevisionStatus.PUBLISHED.value,
        properties=[],
        source_bindings=[],
        links=[],
        source_nodes=[],
        computed_properties=[],
        layout_state={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        published_at=datetime.now(UTC),
    )
    return repo.save(revision)


class TestMaterializedRowStorage:
    """Test that materialized rows can be saved and retrieved."""

    def test_save_and_retrieve_rows(self, db_session, seed_entity, seed_published_revision):
        """Repository can save rows and retrieve them by entity + revision."""
        repo = EntityMaterializationRepository(db_session)

        rows = [
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=seed_entity.id,
                revision_id=seed_published_revision.id,
                row_id="row-001",
                row_data={"employee_id": 1, "employee_name": "Alice"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=seed_entity.id,
                revision_id=seed_published_revision.id,
                row_id="row-002",
                row_data={"employee_id": 2, "employee_name": "Bob"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
        ]

        repo.save_rows(seed_entity.id, seed_published_revision.id, rows)

        result = repo.get_rows(seed_entity.id, seed_published_revision.id)
        assert len(result) == 2
        row_ids = {r.row_id for r in result}
        assert "row-001" in row_ids
        assert "row-002" in row_ids

    def test_rows_excludes_tombstones_by_default(self, db_session, seed_entity, seed_published_revision):
        """get_rows excludes tombstones unless include_tombstones=True."""
        repo = EntityMaterializationRepository(db_session)

        rows = [
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=seed_entity.id,
                revision_id=seed_published_revision.id,
                row_id="row-001",
                row_data={"employee_id": 1},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=seed_entity.id,
                revision_id=seed_published_revision.id,
                row_id="row-002",
                row_data={"employee_id": 2},
                is_tombstone=True,
                materialized_at=datetime.now(UTC),
                deleted_at=datetime.now(UTC),
            ),
        ]

        repo.save_rows(seed_entity.id, seed_published_revision.id, rows)

        normal = repo.get_rows(seed_entity.id, seed_published_revision.id)
        assert len(normal) == 1
        assert normal[0].row_id == "row-001"

        audit = repo.get_rows(seed_entity.id, seed_published_revision.id, include_tombstones=True)
        assert len(audit) == 2

    def test_get_rows_filters_by_entity_and_revision(self, db_session, seed_entity, seed_published_revision):
        """get_rows returns only rows matching entity_id and revision_id."""
        repo = EntityMaterializationRepository(db_session)

        other_revision = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=2,
            status=RevisionStatus.PUBLISHED.value,
            properties=[],
            source_bindings=[],
            links=[],
            source_nodes=[],
            computed_properties=[],
            layout_state={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            published_at=datetime.now(UTC),
        )
        EntityRevisionRepository(db_session).save(other_revision)

        repo.save_rows(
            seed_entity.id,
            seed_published_revision.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=seed_published_revision.id,
                    row_id="row-001",
                    row_data={"employee_id": 1},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                )
            ],
        )
        repo.save_rows(
            seed_entity.id,
            other_revision.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=other_revision.id,
                    row_id="row-002",
                    row_data={"employee_id": 2},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                )
            ],
        )

        rev1_rows = repo.get_rows(seed_entity.id, seed_published_revision.id)
        assert len(rev1_rows) == 1
        assert rev1_rows[0].row_id == "row-001"

    def test_get_single_row(self, db_session, seed_entity, seed_published_revision):
        """get_row returns a single row by entity_id + row_id."""
        repo = EntityMaterializationRepository(db_session)

        rows = [
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=seed_entity.id,
                revision_id=seed_published_revision.id,
                row_id="row-001",
                row_data={"employee_id": 1},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
        ]
        repo.save_rows(seed_entity.id, seed_published_revision.id, rows)

        result = repo.get_row(seed_entity.id, "row-001")
        assert result is not None
        assert result.row_id == "row-001"
        assert result.row_data["employee_id"] == 1

        missing = repo.get_row(seed_entity.id, "row-999")
        assert missing is None

    def test_tombstone_missing_rows(self, db_session, seed_entity, seed_published_revision):
        """tombstone_missing_rows marks old rows as tombstones when not in new set."""
        repo = EntityMaterializationRepository(db_session)

        # First run: rows A and B
        repo.save_rows(
            seed_entity.id,
            seed_published_revision.id,
            [
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=seed_published_revision.id,
                    row_id="row-A",
                    row_data={"employee_id": 1},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                ),
                EntityMaterializedRow(
                    id=str(uuid.uuid4()),
                    entity_id=seed_entity.id,
                    revision_id=seed_published_revision.id,
                    row_id="row-B",
                    row_data={"employee_id": 2},
                    is_tombstone=False,
                    materialized_at=datetime.now(UTC),
                ),
            ],
        )

        # Second run: only row A. Mark B as tombstone.
        repo.tombstone_missing_rows(seed_entity.id, seed_published_revision.id, {"row-A"})

        all_rows = repo.get_rows(seed_entity.id, seed_published_revision.id, include_tombstones=True)
        assert len(all_rows) == 2

        tombstoned = [r for r in all_rows if r.is_tombstone]
        assert len(tombstoned) == 1
        assert tombstoned[0].row_id == "row-B"

        active = repo.get_rows(seed_entity.id, seed_published_revision.id)
        assert len(active) == 1
        assert active[0].row_id == "row-A"
