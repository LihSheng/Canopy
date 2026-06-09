"""Unit tests for publish-time link validation."""

import uuid
from datetime import UTC, datetime

import pytest

from common.errors import ValidationError
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


def _make_published_revision(db_session, entity_id, properties=None, links=None):
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
    rev_repo.save(draft)
    service = EntityRevisionService(rev_repo, ObjectTypeRepository(db_session))
    return service.publish_draft(entity_id, "test-tenant-1")


class TestEntityLinkPublishValidation:
    def test_publish_fails_invalid_cardinality(self, db_session, tenant_context):
        from unittest.mock import patch

        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_1")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_1")
        _make_published_revision(
            db_session, target_id, properties=[EntityProperty(property_id="t1", property_key="id", display_name="ID")]
        )
        rev_repo = EntityRevisionRepository(db_session)
        obj_repo = ObjectTypeRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        # Create a draft in-memory with an invalid cardinality dict (bypassing EntityLink constructor)
        bad_draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
            source_bindings=[],
            links=[
                {
                    "link_id": "link-1",
                    "display_name": "Bad",
                    "source_property_key": "name",
                    "target_entity_id": target_id,
                    "target_property_key": "id",
                    "cardinality": "M:M",
                    "is_optional": False,
                    "is_active": True,
                }
            ],
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

        with patch.object(rev_repo, "get_draft", return_value=bad_draft):
            with pytest.raises(ValidationError) as exc_info:
                service.publish_draft(source_id, tenant_context.tenant_id)
        assert "Invalid cardinality" in str(exc_info.value)

    def test_publish_fails_target_not_published(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_2")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_2")
        # target NOT published
        rev_repo = EntityRevisionRepository(db_session)
        obj_repo = ObjectTypeRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
            source_bindings=[],
            links=[
                EntityLink(
                    link_id="link-1",
                    display_name="Target",
                    source_property_key="name",
                    target_entity_id=target_id,
                    target_property_key="id",
                    cardinality=LinkCardinality.ONE_TO_ONE.value,
                ).to_dict()
            ],
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

        with pytest.raises(ValidationError) as exc_info:
            service.publish_draft(source_id, tenant_context.tenant_id)
        assert "not published" in str(exc_info.value)

    def test_publish_fails_source_property_missing(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_3")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_3")
        _make_published_revision(
            db_session, target_id, properties=[EntityProperty(property_id="t1", property_key="id", display_name="ID")]
        )
        rev_repo = EntityRevisionRepository(db_session)
        obj_repo = ObjectTypeRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
            source_bindings=[],
            links=[
                EntityLink(
                    link_id="link-1",
                    display_name="Target",
                    source_property_key="nonexistent_key",
                    target_entity_id=target_id,
                    target_property_key="id",
                    cardinality=LinkCardinality.ONE_TO_ONE.value,
                ).to_dict()
            ],
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

        with pytest.raises(ValidationError) as exc_info:
            service.publish_draft(source_id, tenant_context.tenant_id)
        assert "source_property_key" in str(exc_info.value)

    def test_publish_fails_target_property_missing(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_4")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_4")
        _make_published_revision(
            db_session, target_id, properties=[EntityProperty(property_id="t1", property_key="id", display_name="ID")]
        )
        rev_repo = EntityRevisionRepository(db_session)
        obj_repo = ObjectTypeRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
            source_bindings=[],
            links=[
                EntityLink(
                    link_id="link-1",
                    display_name="Target",
                    source_property_key="name",
                    target_entity_id=target_id,
                    target_property_key="nonexistent_key",
                    cardinality=LinkCardinality.ONE_TO_ONE.value,
                ).to_dict()
            ],
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

        with pytest.raises(ValidationError) as exc_info:
            service.publish_draft(source_id, tenant_context.tenant_id)
        assert "target_property_key" in str(exc_info.value)

    def test_publish_succeeds_valid_one_to_one(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_5")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_5")
        _make_published_revision(
            db_session, target_id, properties=[EntityProperty(property_id="t1", property_key="id", display_name="ID")]
        )
        rev_repo = EntityRevisionRepository(db_session)
        obj_repo = ObjectTypeRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
            source_bindings=[],
            links=[
                EntityLink(
                    link_id="link-1",
                    display_name="Target",
                    source_property_key="name",
                    target_entity_id=target_id,
                    target_property_key="id",
                    cardinality=LinkCardinality.ONE_TO_ONE.value,
                ).to_dict()
            ],
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

        published = service.publish_draft(source_id, tenant_context.tenant_id)
        assert published.status == RevisionStatus.PUBLISHED.value

    def test_publish_succeeds_optional_one_to_many(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_6")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_6")
        _make_published_revision(
            db_session, target_id, properties=[EntityProperty(property_id="t1", property_key="id", display_name="ID")]
        )
        rev_repo = EntityRevisionRepository(db_session)
        obj_repo = ObjectTypeRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
            source_bindings=[],
            links=[
                EntityLink(
                    link_id="link-1",
                    display_name="Target",
                    source_property_key="name",
                    target_entity_id=target_id,
                    target_property_key="id",
                    cardinality=LinkCardinality.ONE_TO_MANY.value,
                    is_optional=True,
                ).to_dict()
            ],
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

        published = service.publish_draft(source_id, tenant_context.tenant_id)
        assert published.status == RevisionStatus.PUBLISHED.value

    def test_publish_fails_required_link_target_unpublished(self, db_session, tenant_context):
        source_id = _make_entity(db_session, tenant_context.tenant_id, "source_7")
        target_id = _make_entity(db_session, tenant_context.tenant_id, "target_7")
        # target has a draft but NOT published
        rev_repo = EntityRevisionRepository(db_session)
        obj_repo = ObjectTypeRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        target_draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=target_id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[EntityProperty(property_id="t1", property_key="id", display_name="ID")],
            source_bindings=[],
            links=[],
            source_nodes=[
                {"source_id": "s1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["id"]}
            ],
            computed_properties=[],
            layout_state={},
            lock_holder_id="test-user",
            locked_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        rev_repo.save(target_draft)

        source_draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=source_id,
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
            source_bindings=[],
            links=[
                EntityLink(
                    link_id="link-1",
                    display_name="Target",
                    source_property_key="name",
                    target_entity_id=target_id,
                    target_property_key="id",
                    cardinality=LinkCardinality.ONE_TO_ONE.value,
                    is_optional=False,
                ).to_dict()
            ],
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
        rev_repo.save(source_draft)

        with pytest.raises(ValidationError) as exc_info:
            service.publish_draft(source_id, tenant_context.tenant_id)
        assert "not published" in str(exc_info.value)
