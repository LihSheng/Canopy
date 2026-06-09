"""Unit tests for entity link CRUD inside draft revisions."""

import uuid
from datetime import UTC, datetime

import pytest

from common.errors import NotFoundError
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


def _make_entity(db_session, tenant_id, entity_id=None):
    entity_id = entity_id or str(uuid.uuid4())
    obj_repo = ObjectTypeRepository(db_session)
    obj_repo.save(
        ObjectType(
            id=entity_id,
            tenant_id=tenant_id,
            object_type_key=f"link_test_{entity_id[:8]}",
            display_name="Link Test Entity",
            description="Entity for link CRUD tests",
            created_at=datetime.now(UTC),
        )
    )
    return entity_id


def _make_draft(db_session, entity_id, properties=None, links=None):
    rev_repo = EntityRevisionRepository(db_session)
    draft = EntityRevision(
        id=str(uuid.uuid4()),
        entity_id=entity_id,
        revision_number=1,
        status=RevisionStatus.DRAFT.value,
        properties=properties or [],
        source_bindings=[],
        links=links or [],
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
    return rev_repo.save(draft)


class TestEntityLinkCrud:
    def test_add_link_to_draft(self, db_session, tenant_context):
        entity_id = _make_entity(db_session, tenant_context.tenant_id)
        _make_draft(db_session, entity_id)
        obj_repo = ObjectTypeRepository(db_session)
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        link = EntityLink(
            link_id="link-1",
            display_name="Manager",
            source_property_key="manager_id",
            target_entity_id="target-entity-1",
            target_property_key="employee_id",
            cardinality=LinkCardinality.ONE_TO_ONE.value,
        )
        updated = service.add_link(entity_id, tenant_context.tenant_id, link, lock_holder_id="test-user")
        assert len(updated.links) == 1
        assert updated.links[0].link_id == "link-1"
        assert updated.links[0].display_name == "Manager"

    def test_update_link_in_draft(self, db_session, tenant_context):
        entity_id = _make_entity(db_session, tenant_context.tenant_id)
        link = EntityLink(
            link_id="link-1",
            display_name="Manager",
            source_property_key="manager_id",
            target_entity_id="target-entity-1",
            target_property_key="employee_id",
            cardinality=LinkCardinality.ONE_TO_ONE.value,
        )
        _make_draft(db_session, entity_id, links=[link])
        obj_repo = ObjectTypeRepository(db_session)
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        updated = service.update_link(
            entity_id,
            tenant_context.tenant_id,
            "link-1",
            {"display_name": "Updated Manager", "is_optional": True},
            lock_holder_id="test-user",
        )
        assert updated.links[0].display_name == "Updated Manager"
        assert updated.links[0].is_optional is True

    def test_remove_link_from_draft(self, db_session, tenant_context):
        entity_id = _make_entity(db_session, tenant_context.tenant_id)
        link = EntityLink(
            link_id="link-1",
            display_name="Manager",
            source_property_key="manager_id",
            target_entity_id="target-entity-1",
            target_property_key="employee_id",
            cardinality=LinkCardinality.ONE_TO_ONE.value,
        )
        _make_draft(db_session, entity_id, links=[link])
        obj_repo = ObjectTypeRepository(db_session)
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        updated = service.remove_link(entity_id, tenant_context.tenant_id, "link-1", lock_holder_id="test-user")
        assert len(updated.links) == 0

    def test_list_links(self, db_session, tenant_context):
        entity_id = _make_entity(db_session, tenant_context.tenant_id)
        link = EntityLink(
            link_id="link-1",
            display_name="Manager",
            source_property_key="manager_id",
            target_entity_id="target-entity-1",
            target_property_key="employee_id",
            cardinality=LinkCardinality.ONE_TO_ONE.value,
        )
        _make_draft(db_session, entity_id, links=[link])
        obj_repo = ObjectTypeRepository(db_session)
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        links = service.list_links(entity_id, tenant_context.tenant_id)
        assert len(links) == 1
        assert links[0].link_id == "link-1"

    def test_link_crud_rejected_on_published(self, db_session, tenant_context):
        entity_id = _make_entity(db_session, tenant_context.tenant_id)
        obj_repo = ObjectTypeRepository(db_session)
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        # Create initial draft with a source node and property so publish succeeds
        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=entity_id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
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
        service.publish_draft(entity_id, tenant_context.tenant_id)

        link = EntityLink(
            link_id="link-1",
            display_name="Manager",
            source_property_key="manager_id",
            target_entity_id="target-entity-1",
            target_property_key="employee_id",
            cardinality=LinkCardinality.ONE_TO_ONE.value,
        )
        with pytest.raises(NotFoundError):
            service.add_link(entity_id, tenant_context.tenant_id, link, lock_holder_id="test-user")

    def test_link_preserved_through_fork(self, db_session, tenant_context):
        entity_id = _make_entity(db_session, tenant_context.tenant_id)
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_fork")
        obj_repo = ObjectTypeRepository(db_session)
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        # Publish target first
        target_draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=target_id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[EntityProperty(property_id="t1", property_key="employee_id", display_name="Employee ID")],
            source_bindings=[],
            links=[],
            source_nodes=[
                {
                    "source_id": "s1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["employee_id"],
                }
            ],
            computed_properties=[],
            layout_state={},
            lock_holder_id="test-user",
            locked_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        rev_repo.save(target_draft)
        service.publish_draft(target_id, tenant_context.tenant_id)

        # Create and publish initial revision with a link
        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=entity_id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[
                EntityProperty(property_id="p1", property_key="name", display_name="Name"),
                EntityProperty(property_id="p2", property_key="manager_id", display_name="Manager ID"),
            ],
            source_bindings=[],
            links=[
                EntityLink(
                    link_id="link-1",
                    display_name="Manager",
                    source_property_key="manager_id",
                    target_entity_id=target_id,
                    target_property_key="employee_id",
                    cardinality=LinkCardinality.ONE_TO_ONE.value,
                ).to_dict()
            ],
            source_nodes=[
                {
                    "source_id": "s1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["name", "manager_id"],
                }
            ],
            computed_properties=[],
            layout_state={},
            lock_holder_id="test-user",
            locked_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        rev_repo.save(draft)
        service.publish_draft(entity_id, tenant_context.tenant_id)

        new_draft = service.fork_draft(entity_id, "test-user-2", tenant_context.tenant_id)
        assert len(new_draft.links) == 1
        assert isinstance(new_draft.links[0], EntityLink)
        assert new_draft.links[0].link_id == "link-1"
