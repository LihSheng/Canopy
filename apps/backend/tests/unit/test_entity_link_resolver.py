"""Unit tests for LinkResolverService."""

import uuid
from datetime import UTC, datetime

import pytest

from common.errors import NotFoundError
from entity_link_resolver.service import LinkResolverService
from entity_materialization.domain import EntityMaterializedRow
from entity_revision.domain import EntityLink, EntityProperty, EntityRevision, LinkCardinality, RevisionStatus
from entity_revision.repository import EntityRevisionRepository
from entity_revision.service import EntityRevisionService
from semantic.domain import ObjectType
from semantic.repository import ObjectTypeRepository

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def tenant_context():
    from context.tenant_context import TenantContext, set_current_tenant_context

    ctx = TenantContext(
        tenant_id="test-tenant-1",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx)
    return ctx


def _make_entity(db_session, tenant_id, key, entity_id=None):
    entity_id = entity_id or str(uuid.uuid4())
    obj_repo = ObjectTypeRepository(db_session)
    obj_repo.save(
        ObjectType(
            id=entity_id,
            tenant_id=tenant_id,
            object_type_key=key,
            display_name="Test Entity",
            description="Test",
            created_at=datetime.now(UTC),
        )
    )
    return entity_id


def _make_published_revision(db_session, entity_id, properties=None):
    rev_repo = EntityRevisionRepository(db_session)
    draft = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=entity_id,
        revision_number=1,
        status=RevisionStatus.DRAFT.value,
        properties=properties or [],
        source_bindings=[],
        links=[],
        source_nodes=[
            {"source_id": "s1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["name"]}
        ],
        computed_properties=[],
        layout_state={},
        lock_holder_id="test-user",
        locked_at=datetime.now(UTC),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    rev_repo.save(draft)
    service = EntityRevisionService(rev_repo, ObjectTypeRepository(db_session))
    return service.publish_draft(entity_id, "test-tenant-1")


class MockMaterializationService:
    """Mock materialization service for unit tests."""

    def __init__(self, rows=None):
        self._rows = rows or []

    def get_rows(self, entity_id, revision_id=None, include_tombstones=False):
        return [r for r in self._rows if r.entity_id == entity_id]

    def get_row(self, entity_id, row_id):
        for r in self._rows:
            if r.entity_id == entity_id and r.row_id == row_id:
                return r
        return None


class TestLinkResolverService:
    def test_resolve_one_to_one(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_1")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_1")
        target_rev = _make_published_revision(
            db_session, target_id, properties=[EntityProperty(property_id="t1", property_key="id", display_name="ID")]
        )
        rev_repo = EntityRevisionRepository(db_session)
        source_rev = _make_published_revision(
            db_session,
            source_id,
            properties=[EntityProperty(property_id="p1", property_key="manager_id", display_name="Manager ID")],
        )
        # Add link to source revision
        source_rev = rev_repo.get(source_rev.id)
        source_rev.links = [
            EntityLink(
                link_id="link-1",
                display_name="Manager",
                source_property_key="manager_id",
                target_entity_id=target_id,
                target_property_key="id",
                cardinality=LinkCardinality.ONE_TO_ONE.value,
            )
        ]
        rev_repo.save(source_rev)

        target_rows = [
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=target_id,
                revision_id=target_rev.id,
                row_id="mgr-1",
                row_data={"id": "mgr-1", "name": "Alice"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
        ]
        mock_mat = MockMaterializationService(target_rows)
        resolver = LinkResolverService(rev_repo, mock_mat)

        source_row = EntityMaterializedRow(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_id=source_rev.id,
            row_id="emp-1",
            row_data={"manager_id": "mgr-1"},
            is_tombstone=False,
            materialized_at=datetime.now(UTC),
        )

        result = resolver.resolve_link(source_id, "link-1", source_row, revision_id=source_rev.id)
        assert result is not None
        assert result.row_id == "mgr-1"
        assert result.row_data["name"] == "Alice"

    def test_resolve_one_to_many(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_2")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_2")
        target_rev = _make_published_revision(
            db_session,
            target_id,
            properties=[EntityProperty(property_id="t1", property_key="dept_id", display_name="Dept ID")],
        )
        rev_repo = EntityRevisionRepository(db_session)
        source_rev = _make_published_revision(
            db_session,
            source_id,
            properties=[EntityProperty(property_id="p1", property_key="dept_id", display_name="Dept ID")],
        )
        source_rev = rev_repo.get(source_rev.id)
        source_rev.links = [
            EntityLink(
                link_id="link-1",
                display_name="Employees",
                source_property_key="dept_id",
                target_entity_id=target_id,
                target_property_key="dept_id",
                cardinality=LinkCardinality.ONE_TO_MANY.value,
            )
        ]
        rev_repo.save(source_rev)

        target_rows = [
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=target_id,
                revision_id=target_rev.id,
                row_id="emp-1",
                row_data={"dept_id": "d1", "name": "Alice"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=target_id,
                revision_id=target_rev.id,
                row_id="emp-2",
                row_data={"dept_id": "d1", "name": "Bob"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=target_id,
                revision_id=target_rev.id,
                row_id="emp-3",
                row_data={"dept_id": "d2", "name": "Carol"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
        ]
        mock_mat = MockMaterializationService(target_rows)
        resolver = LinkResolverService(rev_repo, mock_mat)

        source_row = EntityMaterializedRow(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_id=source_rev.id,
            row_id="dept-1",
            row_data={"dept_id": "d1"},
            is_tombstone=False,
            materialized_at=datetime.now(UTC),
        )

        result = resolver.resolve_link(source_id, "link-1", source_row, revision_id=source_rev.id)
        assert isinstance(result, list)
        assert len(result) == 2
        assert {r.row_id for r in result} == {"emp-1", "emp-2"}

    def test_resolve_optional_returns_none_when_target_not_published(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_3")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_3")
        rev_repo = EntityRevisionRepository(db_session)
        source_rev = _make_published_revision(
            db_session,
            source_id,
            properties=[EntityProperty(property_id="p1", property_key="manager_id", display_name="Manager ID")],
        )
        source_rev = rev_repo.get(source_rev.id)
        source_rev.links = [
            EntityLink(
                link_id="link-1",
                display_name="Manager",
                source_property_key="manager_id",
                target_entity_id=target_id,
                target_property_key="id",
                cardinality=LinkCardinality.ONE_TO_ONE.value,
                is_optional=True,
            )
        ]
        rev_repo.save(source_rev)

        mock_mat = MockMaterializationService([])
        resolver = LinkResolverService(rev_repo, mock_mat)

        source_row = EntityMaterializedRow(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_id=source_rev.id,
            row_id="emp-1",
            row_data={"manager_id": "mgr-1"},
            is_tombstone=False,
            materialized_at=datetime.now(UTC),
        )

        result = resolver.resolve_link(source_id, "link-1", source_row, revision_id=source_rev.id)
        assert result is None

    def test_resolve_optional_returns_none_when_no_target_rows(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_4")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_4")
        _make_published_revision(
            db_session, target_id, properties=[EntityProperty(property_id="t1", property_key="id", display_name="ID")]
        )
        rev_repo = EntityRevisionRepository(db_session)
        source_rev = _make_published_revision(
            db_session,
            source_id,
            properties=[EntityProperty(property_id="p1", property_key="manager_id", display_name="Manager ID")],
        )
        source_rev = rev_repo.get(source_rev.id)
        source_rev.links = [
            EntityLink(
                link_id="link-1",
                display_name="Manager",
                source_property_key="manager_id",
                target_entity_id=target_id,
                target_property_key="id",
                cardinality=LinkCardinality.ONE_TO_ONE.value,
                is_optional=True,
            )
        ]
        rev_repo.save(source_rev)

        mock_mat = MockMaterializationService([])
        resolver = LinkResolverService(rev_repo, mock_mat)

        source_row = EntityMaterializedRow(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_id=source_rev.id,
            row_id="emp-1",
            row_data={"manager_id": "mgr-1"},
            is_tombstone=False,
            materialized_at=datetime.now(UTC),
        )

        result = resolver.resolve_link(source_id, "link-1", source_row, revision_id=source_rev.id)
        assert result is None

    def test_resolve_required_raises_when_target_not_published(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_5")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_5")
        rev_repo = EntityRevisionRepository(db_session)
        source_rev = _make_published_revision(
            db_session,
            source_id,
            properties=[EntityProperty(property_id="p1", property_key="manager_id", display_name="Manager ID")],
        )
        source_rev = rev_repo.get(source_rev.id)
        source_rev.links = [
            EntityLink(
                link_id="link-1",
                display_name="Manager",
                source_property_key="manager_id",
                target_entity_id=target_id,
                target_property_key="id",
                cardinality=LinkCardinality.ONE_TO_ONE.value,
                is_optional=False,
            )
        ]
        rev_repo.save(source_rev)

        mock_mat = MockMaterializationService([])
        resolver = LinkResolverService(rev_repo, mock_mat)

        source_row = EntityMaterializedRow(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_id=source_rev.id,
            row_id="emp-1",
            row_data={"manager_id": "mgr-1"},
            is_tombstone=False,
            materialized_at=datetime.now(UTC),
        )

        with pytest.raises(NotFoundError):
            resolver.resolve_link(source_id, "link-1", source_row, revision_id=source_rev.id)

    def test_resolve_batch(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_6")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_6")
        target_rev = _make_published_revision(
            db_session, target_id, properties=[EntityProperty(property_id="t1", property_key="id", display_name="ID")]
        )
        rev_repo = EntityRevisionRepository(db_session)
        source_rev = _make_published_revision(
            db_session,
            source_id,
            properties=[EntityProperty(property_id="p1", property_key="manager_id", display_name="Manager ID")],
        )
        source_rev = rev_repo.get(source_rev.id)
        source_rev.links = [
            EntityLink(
                link_id="link-1",
                display_name="Manager",
                source_property_key="manager_id",
                target_entity_id=target_id,
                target_property_key="id",
                cardinality=LinkCardinality.ONE_TO_ONE.value,
            )
        ]
        rev_repo.save(source_rev)

        target_rows = [
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=target_id,
                revision_id=target_rev.id,
                row_id="mgr-1",
                row_data={"id": "mgr-1", "name": "Alice"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=target_id,
                revision_id=target_rev.id,
                row_id="mgr-2",
                row_data={"id": "mgr-2", "name": "Bob"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
        ]
        mock_mat = MockMaterializationService(target_rows)
        resolver = LinkResolverService(rev_repo, mock_mat)

        source_rows = [
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=source_id,
                revision_id=source_rev.id,
                row_id="emp-1",
                row_data={"manager_id": "mgr-1"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
            EntityMaterializedRow(
                id=str(uuid.uuid4()),
                entity_id=source_id,
                revision_id=source_rev.id,
                row_id="emp-2",
                row_data={"manager_id": "mgr-2"},
                is_tombstone=False,
                materialized_at=datetime.now(UTC),
            ),
        ]

        results = resolver.resolve_link_batch(source_id, "link-1", source_rows, revision_id=source_rev.id)
        assert results["emp-1"].row_id == "mgr-1"
        assert results["emp-2"].row_id == "mgr-2"
