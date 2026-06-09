"""Unit tests for EntityMaterializationService — materialization logic."""

import uuid
from datetime import UTC, datetime

import pytest

from common.errors import NotFoundError
from entity_materialization.repository import EntityMaterializationRepository
from entity_materialization.service import EntityMaterializationService
from entity_revision.domain import EntityProperty, EntityRevision, RevisionStatus, SourceBinding
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
        object_type_key="mat_svc_entity",
        display_name="Materialization Service Entity",
        description="Entity for materialization service tests",
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
        properties=[
            EntityProperty(
                property_id="prop-001",
                property_key="employee_id",
                display_name="Employee ID",
                semantic_type="integer",
                is_required=True,
                is_primary_key=True,
                sort_order=1,
            ),
            EntityProperty(
                property_id="prop-002",
                property_key="employee_name",
                display_name="Employee Name",
                semantic_type="string",
                is_required=True,
                sort_order=2,
            ),
            EntityProperty(
                property_id="prop-003",
                property_key="department",
                display_name="Department",
                semantic_type="string",
                is_required=False,
                sort_order=3,
            ),
        ],
        source_bindings=[
            SourceBinding(
                property_key="employee_id",
                source_node_id="src-1",
                source_field_name="id",
            ),
            SourceBinding(
                property_key="employee_name",
                source_node_id="src-1",
                source_field_name="name",
            ),
            SourceBinding(
                property_key="department",
                source_node_id="src-1",
                source_field_name="dept",
            ),
        ],
        links=[],
        source_nodes=[
            {
                "source_id": "src-1",
                "source_type": "dataset_table",
                "name": "employees",
                "reference_id": "ds-001",
                "fields": ["id", "name", "dept"],
            }
        ],
        computed_properties=[],
        layout_state={},
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        published_at=datetime.now(UTC),
    )
    return repo.save(revision)


def _make_service(db_session, revision, source_data=None):
    """Build a service with an optional mock source_data reader."""
    revision_repo = EntityRevisionRepository(db_session)
    mat_repo = EntityMaterializationRepository(db_session)

    def _reader(source_node):
        if source_data is not None:
            return source_data
        return []

    return EntityMaterializationService(
        revision_repo=revision_repo,
        materialization_repo=mat_repo,
        source_data_reader=_reader,
    )


class TestMaterializeEntity:
    """Test the full materialization pipeline."""

    def test_materialize_reads_source_and_produces_rows(self, db_session, seed_entity, seed_published_revision):
        """materialize_entity reads source rows and writes entity rows."""
        source_data = [
            {"id": 1, "name": "Alice", "dept": "Engineering"},
            {"id": 2, "name": "Bob", "dept": "Sales"},
        ]
        service = _make_service(db_session, seed_published_revision, source_data=source_data)

        stats = service.materialize_entity(seed_entity.id, seed_published_revision.id)

        assert stats["rows_inserted"] == 2
        assert stats["rows_updated"] == 0
        assert stats["rows_tombstoned"] == 0

        rows = service.get_rows(seed_entity.id, seed_published_revision.id)
        assert len(rows) == 2
        row_by_id = {r.row_id: r.row_data for r in rows}
        assert row_by_id["1"]["employee_id"] == 1
        assert row_by_id["1"]["employee_name"] == "Alice"
        assert row_by_id["2"]["department"] == "Sales"

    def test_materialize_full_replace_updates_existing_rows(self, db_session, seed_entity, seed_published_revision):
        """Second materialization updates rows that already exist."""
        source_data_v1 = [
            {"id": 1, "name": "Alice", "dept": "Engineering"},
        ]
        service = _make_service(db_session, seed_published_revision, source_data=source_data_v1)
        service.materialize_entity(seed_entity.id, seed_published_revision.id)

        source_data_v2 = [
            {"id": 1, "name": "Alice Updated", "dept": "Product"},
        ]
        service2 = _make_service(db_session, seed_published_revision, source_data=source_data_v2)
        stats = service2.materialize_entity(seed_entity.id, seed_published_revision.id)

        assert stats["rows_inserted"] == 0
        assert stats["rows_updated"] == 1
        assert stats["rows_tombstoned"] == 0

        rows = service2.get_rows(seed_entity.id, seed_published_revision.id)
        assert len(rows) == 1
        assert rows[0].row_data["employee_name"] == "Alice Updated"
        assert rows[0].row_data["department"] == "Product"

    def test_missing_rows_become_tombstones(self, db_session, seed_entity, seed_published_revision):
        """Rows in old materialization but not in new source become tombstones."""
        source_data_v1 = [
            {"id": 1, "name": "Alice", "dept": "Engineering"},
            {"id": 2, "name": "Bob", "dept": "Sales"},
        ]
        service = _make_service(db_session, seed_published_revision, source_data=source_data_v1)
        service.materialize_entity(seed_entity.id, seed_published_revision.id)

        source_data_v2 = [
            {"id": 1, "name": "Alice", "dept": "Engineering"},
        ]
        service2 = _make_service(db_session, seed_published_revision, source_data=source_data_v2)
        stats = service2.materialize_entity(seed_entity.id, seed_published_revision.id)

        assert stats["rows_inserted"] == 0
        assert stats["rows_updated"] == 1
        assert stats["rows_tombstoned"] == 1

        active_rows = service2.get_rows(seed_entity.id, seed_published_revision.id)
        assert len(active_rows) == 1
        assert active_rows[0].row_id == "1"

        audit_rows = service2.get_rows(seed_entity.id, seed_published_revision.id, include_tombstones=True)
        assert len(audit_rows) == 2
        tombstoned = [r for r in audit_rows if r.is_tombstone]
        assert len(tombstoned) == 1
        assert tombstoned[0].row_id == "2"
        assert tombstoned[0].row_data["employee_name"] == "Bob"  # preserved

    def test_tombstones_hidden_from_normal_reads(self, db_session, seed_entity, seed_published_revision):
        """Default get_rows excludes tombstones."""
        source_data = [
            {"id": 1, "name": "Alice", "dept": "Engineering"},
        ]
        service = _make_service(db_session, seed_published_revision, source_data=source_data)
        service.materialize_entity(seed_entity.id, seed_published_revision.id)

        # Manually tombstone a row
        mat_repo = EntityMaterializationRepository(db_session)
        mat_repo.tombstone_missing_rows(seed_entity.id, seed_published_revision.id, set())

        normal = service.get_rows(seed_entity.id, seed_published_revision.id)
        assert len(normal) == 0

        audit = service.get_rows(seed_entity.id, seed_published_revision.id, include_tombstones=True)
        assert len(audit) == 1
        assert audit[0].is_tombstone is True

    def test_missing_source_field_produces_null(self, db_session, seed_entity, seed_published_revision):
        """If a bound source field is missing, the entity property is null."""
        source_data = [
            {"id": 1, "name": "Alice"},  # missing "dept"
        ]
        service = _make_service(db_session, seed_published_revision, source_data=source_data)
        service.materialize_entity(seed_entity.id, seed_published_revision.id)

        rows = service.get_rows(seed_entity.id, seed_published_revision.id)
        assert len(rows) == 1
        assert rows[0].row_data["department"] is None

    def test_one_active_source_binding_used(self, db_session, seed_entity):
        """Only one source binding per property is used (the active one)."""
        repo = EntityRevisionRepository(db_session)
        revision = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=seed_entity.id,
            revision_number=1,
            status=RevisionStatus.PUBLISHED.value,
            properties=[
                EntityProperty(
                    property_id="prop-001",
                    property_key="employee_id",
                    display_name="Employee ID",
                    semantic_type="integer",
                    is_required=True,
                    is_primary_key=True,
                    sort_order=1,
                ),
            ],
            source_bindings=[
                SourceBinding(
                    property_key="employee_id",
                    source_node_id="src-1",
                    source_field_name="id",
                ),
            ],
            links=[],
            source_nodes=[
                {
                    "source_id": "src-1",
                    "source_type": "dataset_table",
                    "name": "employees",
                    "reference_id": "ds-001",
                    "fields": ["id"],
                }
            ],
            computed_properties=[],
            layout_state={},
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            published_at=datetime.now(UTC),
        )
        repo.save(revision)

        source_data = [{"id": 42}]
        service = _make_service(db_session, revision, source_data=source_data)
        stats = service.materialize_entity(seed_entity.id, revision.id)

        assert stats["rows_inserted"] == 1
        rows = service.get_rows(seed_entity.id, revision.id)
        assert rows[0].row_data["employee_id"] == 42

    def test_materialize_entity_not_found_raises(self, db_session):
        """materialize_entity raises NotFoundError for missing entity."""
        revision_repo = EntityRevisionRepository(db_session)
        mat_repo = EntityMaterializationRepository(db_session)
        service = EntityMaterializationService(
            revision_repo=revision_repo,
            materialization_repo=mat_repo,
            source_data_reader=lambda sn: [],
        )
        with pytest.raises(NotFoundError):
            service.materialize_entity("nonexistent-entity", "nonexistent-revision")

    def test_get_row_single(self, db_session, seed_entity, seed_published_revision):
        """get_row returns a single materialized row."""
        source_data = [{"id": 1, "name": "Alice", "dept": "Engineering"}]
        service = _make_service(db_session, seed_published_revision, source_data=source_data)
        service.materialize_entity(seed_entity.id, seed_published_revision.id)

        row = service.get_row(seed_entity.id, "1")
        assert row is not None
        assert row.row_data["employee_name"] == "Alice"

        missing = service.get_row(seed_entity.id, "999")
        assert missing is None
