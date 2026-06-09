"""Unit tests for planned bindings model (Issue 3)."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from entity_revision.domain import (
    EntityProperty,
    EntityRevision,
    RevisionStatus,
    SourceBinding,
)

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def tenant_context():
    ctx = TenantContext(
        tenant_id="test-tenant-1",
        tenant_role="admin",
        membership_status="active",
    )
    set_current_tenant_context(ctx)
    return ctx


class TestPlannedBindingsValidation:
    def test_publish_fails_when_planned_binding_references_unpublished_entity(self, db_session, tenant_context):
        """Publish must reject planned bindings that point to unpublished entities."""
        from context.tenant_context import set_current_tenant_context
        from entity_revision.repository import EntityRevisionRepository
        from entity_revision.service import EntityRevisionService
        from semantic.domain import ObjectType
        from semantic.repository import ObjectTypeRepository

        set_current_tenant_context(tenant_context)

        obj_repo = ObjectTypeRepository(db_session)
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        # Target entity (unpublished)
        target_entity_id = str(uuid.uuid4())
        obj_repo.save(
            ObjectType(
                id=target_entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="target_entity",
                display_name="Target Entity",
                description="Target",
                created_at=datetime.now(UTC),
            )
        )
        # No published revision for target_entity

        # Source entity with a draft that references target_entity in planned_bindings
        source_entity_id = str(uuid.uuid4())
        obj_repo.save(
            ObjectType(
                id=source_entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="source_entity",
                display_name="Source Entity",
                description="Source",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=source_entity_id,
                revision_number=1,
                status=RevisionStatus.DRAFT.value,
                properties=[
                    EntityProperty(
                        property_id="p1",
                        property_key="name",
                        display_name="Name",
                    )
                ],
                source_bindings=[
                    SourceBinding(
                        property_key="name",
                        source_node_id="sn1",
                        source_field_name="name",
                        is_active=True,
                    )
                ],
                planned_bindings=[
                    SourceBinding(
                        property_key="target_ref",
                        source_node_id=target_entity_id,  # references target entity
                        source_field_name="field",
                        is_active=False,
                    )
                ],
                source_nodes=[
                    {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["name"]}
                ],
                computed_properties=[],
                links=[],
                layout_state={},
                lock_holder_id="user-1",
                locked_at=datetime.now(UTC),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )

        with pytest.raises(Exception) as exc_info:
            service.publish_draft(source_entity_id, tenant_context.tenant_id)

        assert "planned" in str(exc_info.value).lower()

    def test_publish_succeeds_when_planned_bindings_reference_published_entities(self, db_session, tenant_context):
        """Publish passes when all planned bindings reference published entities."""
        from context.tenant_context import set_current_tenant_context
        from entity_revision.repository import EntityRevisionRepository
        from entity_revision.service import EntityRevisionService
        from semantic.domain import ObjectType
        from semantic.repository import ObjectTypeRepository

        set_current_tenant_context(tenant_context)

        obj_repo = ObjectTypeRepository(db_session)
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        # Target entity (published)
        target_entity_id = str(uuid.uuid4())
        obj_repo.save(
            ObjectType(
                id=target_entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="target_entity",
                display_name="Target Entity",
                description="Target",
                created_at=datetime.now(UTC),
            )
        )
        rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=target_entity_id,
                revision_number=1,
                status=RevisionStatus.PUBLISHED.value,
                properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
                source_bindings=[],
                planned_bindings=[],
                source_nodes=[
                    {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["name"]}
                ],
                computed_properties=[],
                links=[],
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )

        # Source entity with a draft that references target_entity in planned_bindings
        source_entity_id = str(uuid.uuid4())
        obj_repo.save(
            ObjectType(
                id=source_entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="source_entity",
                display_name="Source Entity",
                description="Source",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=source_entity_id,
                revision_number=1,
                status=RevisionStatus.DRAFT.value,
                properties=[
                    EntityProperty(
                        property_id="p1",
                        property_key="name",
                        display_name="Name",
                    )
                ],
                source_bindings=[
                    SourceBinding(
                        property_key="name",
                        source_node_id="sn1",
                        source_field_name="name",
                        is_active=True,
                    )
                ],
                planned_bindings=[
                    SourceBinding(
                        property_key="target_ref",
                        source_node_id=target_entity_id,
                        source_field_name="field",
                        is_active=False,
                    )
                ],
                source_nodes=[
                    {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["name"]}
                ],
                computed_properties=[],
                links=[],
                layout_state={},
                lock_holder_id="user-1",
                locked_at=datetime.now(UTC),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )

        published = service.publish_draft(source_entity_id, tenant_context.tenant_id)
        assert published.status == RevisionStatus.PUBLISHED.value
        assert len(published.planned_bindings) == 1
        assert published.planned_bindings[0].source_node_id == target_entity_id

    def test_planned_bindings_editable_only_through_draft(self, db_session, tenant_context):
        """Planned bindings cannot be mutated on a published revision."""
        from context.tenant_context import set_current_tenant_context
        from entity_revision.repository import EntityRevisionRepository
        from entity_revision.service import EntityRevisionService
        from semantic.domain import ObjectType
        from semantic.repository import ObjectTypeRepository

        set_current_tenant_context(tenant_context)

        obj_repo = ObjectTypeRepository(db_session)
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        entity_id = str(uuid.uuid4())
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="draft_only",
                display_name="Draft Only",
                description="Draft only test",
                created_at=datetime.now(UTC),
            )
        )

        # Publish directly
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            publish=True,
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["name"]}
            ],
            properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
            source_bindings=[
                SourceBinding(property_key="name", source_node_id="sn1", source_field_name="name", is_active=True)
            ],
        )

        # Attempt to update planned bindings on the published revision (should fail because no draft)
        with pytest.raises(Exception) as exc_info:
            service.update_draft(
                entity_id=entity_id,
                tenant_id=tenant_context.tenant_id,
                planned_bindings=[
                    SourceBinding(property_key="future", source_node_id="sn2", source_field_name="f", is_active=False)
                ],
                lock_holder_id="user-1",
            )

        assert "No active draft" in str(exc_info.value)


class TestPlannedBindingsModel:
    def test_source_binding_has_is_active_flag(self):
        """SourceBinding should carry an is_active flag (default True)."""
        b = SourceBinding(
            property_key="pk",
            source_node_id="sn1",
            source_field_name="fn",
        )
        assert hasattr(b, "is_active")
        assert b.is_active is True

    def test_entity_revision_has_planned_bindings_field(self):
        """EntityRevision should store planned_bindings separately."""
        rev = EntityRevision(
            id="r1",
            entity_id="e1",
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
        )
        assert hasattr(rev, "planned_bindings")
        assert rev.planned_bindings == []

    def test_planned_bindings_can_be_set(self):
        """Planned bindings can be instantiated and assigned."""
        pb = SourceBinding(
            property_key="planned_pk",
            source_node_id="sn2",
            source_field_name="planned_fn",
            is_active=False,
        )
        rev = EntityRevision(
            id="r1",
            entity_id="e1",
            revision_number=1,
            status=RevisionStatus.DRAFT.value,
            planned_bindings=[pb],
        )
        assert len(rev.planned_bindings) == 1
        assert rev.planned_bindings[0].is_active is False

    def test_planned_bindings_survive_fork(self, db_session, tenant_context):
        """Forking a draft should copy planned_bindings from published."""
        from context.tenant_context import set_current_tenant_context
        from entity_revision.repository import EntityRevisionRepository
        from entity_revision.service import EntityRevisionService
        from semantic.domain import ObjectType
        from semantic.repository import ObjectTypeRepository

        set_current_tenant_context(tenant_context)

        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="planned_fork",
                display_name="Planned Fork Test",
                description="Fork test",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=entity_id,
                revision_number=1,
                status=RevisionStatus.PUBLISHED.value,
                properties=[
                    EntityProperty(
                        property_id="p1",
                        property_key="name",
                        display_name="Name",
                    )
                ],
                source_bindings=[
                    SourceBinding(
                        property_key="name",
                        source_node_id="sn1",
                        source_field_name="name",
                        is_active=True,
                    )
                ],
                planned_bindings=[
                    SourceBinding(
                        property_key="future",
                        source_node_id="sn2",
                        source_field_name="future",
                        is_active=False,
                    )
                ],
                source_nodes=[
                    {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["name"]}
                ],
                computed_properties=[],
                links=[],
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )

        service = EntityRevisionService(rev_repo, obj_repo)
        draft = service.fork_draft(
            entity_id=entity_id,
            lock_holder_id="user-1",
            tenant_id=tenant_context.tenant_id,
        )

        assert len(draft.planned_bindings) == 1
        assert draft.planned_bindings[0].property_key == "future"
        assert draft.planned_bindings[0].is_active is False

    def test_planned_bindings_survive_publish(self, db_session, tenant_context):
        """Publishing a draft should preserve planned_bindings in the published revision."""
        from context.tenant_context import set_current_tenant_context
        from entity_revision.repository import EntityRevisionRepository
        from entity_revision.service import EntityRevisionService
        from semantic.domain import ObjectType
        from semantic.repository import ObjectTypeRepository

        set_current_tenant_context(tenant_context)

        obj_repo = ObjectTypeRepository(db_session)
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        # Target entity (published) so planned binding can reference it
        target_entity_id = str(uuid.uuid4())
        obj_repo.save(
            ObjectType(
                id=target_entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="target_entity",
                display_name="Target Entity",
                description="Target",
                created_at=datetime.now(UTC),
            )
        )
        rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=target_entity_id,
                revision_number=1,
                status=RevisionStatus.PUBLISHED.value,
                properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
                source_bindings=[],
                planned_bindings=[],
                source_nodes=[
                    {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["name"]}
                ],
                computed_properties=[],
                links=[],
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )

        entity_id = str(uuid.uuid4())
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="planned_publish",
                display_name="Planned Publish Test",
                description="Publish test",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=entity_id,
                revision_number=1,
                status=RevisionStatus.DRAFT.value,
                properties=[
                    EntityProperty(
                        property_id="p1",
                        property_key="name",
                        display_name="Name",
                    )
                ],
                source_bindings=[
                    SourceBinding(
                        property_key="name",
                        source_node_id="sn1",
                        source_field_name="name",
                        is_active=True,
                    )
                ],
                planned_bindings=[
                    SourceBinding(
                        property_key="future",
                        source_node_id=target_entity_id,
                        source_field_name="future",
                        is_active=False,
                    )
                ],
                source_nodes=[
                    {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["name"]}
                ],
                computed_properties=[],
                links=[],
                layout_state={},
                lock_holder_id="user-1",
                locked_at=datetime.now(UTC),
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
            )
        )

        published = service.publish_draft(entity_id, tenant_context.tenant_id)

        assert published.status == RevisionStatus.PUBLISHED.value
        assert len(published.planned_bindings) == 1
        assert published.planned_bindings[0].property_key == "future"
        assert published.planned_bindings[0].is_active is False
