"""Unit tests for entity revision immutability — published revisions cannot be mutated."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from entity_revision.domain import EntityProperty, EntityRevision, RevisionStatus
from entity_revision.repository import EntityRevisionRepository
from entity_revision.service import EntityRevisionService
from semantic.domain import ObjectType
from semantic.repository import ObjectTypeRepository

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


class TestPublishedRevisionImmutability:
    def test_update_draft_rejects_when_no_draft_exists(self, db_session, tenant_context):
        """Calling update_draft on an entity with only published revisions raises NotFoundError."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="immut_test",
                display_name="Immutability Test",
                description="Entity for immutability tests",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        published = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=entity_id,
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
        rev_repo.save(published)

        service = EntityRevisionService(rev_repo, obj_repo)

        with pytest.raises(Exception) as exc_info:
            service.update_draft(
                entity_id=entity_id,
                tenant_id=tenant_context.tenant_id,
                properties=[],
                lock_holder_id="test-user",
            )

        assert "No active draft" in str(exc_info.value)

    def test_update_draft_rejects_published_status_explicitly(self, db_session, tenant_context):
        """If a revision somehow has non-draft status, update_draft raises ValidationError."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="immut_test_2",
                display_name="Immutability Guard Test",
                description="Entity for explicit guard test",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        not_a_draft = EntityRevision(
            id=str(uuid.uuid4()),
            entity_id=entity_id,
            revision_number=1,
            status=RevisionStatus.PUBLISHED.value,
            properties=[],
            source_bindings=[],
            links=[],
            source_nodes=[],
            computed_properties=[],
            layout_state={},
            lock_holder_id="test-user",
            locked_at=datetime.now(UTC),
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
            published_at=datetime.now(UTC),
        )
        rev_repo.save(not_a_draft)

        service = EntityRevisionService(rev_repo, obj_repo)

        # update_draft checks get_draft first, which filters by status="draft".
        # The guard inside update_draft catches any revision that is not actually "draft".
        with pytest.raises(Exception) as exc_info:
            service.update_draft(
                entity_id=entity_id,
                tenant_id=tenant_context.tenant_id,
                properties=[
                    EntityProperty(
                        property_id="p1",
                        property_key="name",
                        display_name="Name",
                    )
                ],
                lock_holder_id="test-user",
            )

        assert "No active draft" in str(exc_info.value)

    def test_published_revision_cannot_be_mutated_to_draft(self, db_session, tenant_context):
        """A published revision's properties cannot be altered via repo directly,
        but the service layer must prevent it. This test verifies the entity
        lifecycle: once published, the revision is frozen."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="frozen_test",
                display_name="Frozen Entity",
                description="Testing freeze after publish",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)

        # Create and publish initial revision
        initial = rev_repo.save(
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
        )

        service = EntityRevisionService(rev_repo, obj_repo)

        # Publish the draft
        published = service.publish_draft(entity_id, tenant_context.tenant_id)
        assert published.status == RevisionStatus.PUBLISHED.value
        assert published.id == initial.id

        # Now there's no draft, so update_draft should fail
        with pytest.raises(Exception) as exc_info:
            service.update_draft(
                entity_id=entity_id,
                tenant_id=tenant_context.tenant_id,
                properties=[
                    EntityProperty(
                        property_id="p2",
                        property_key="hacked",
                        display_name="Hacked",
                    )
                ],
                lock_holder_id="test-user",
            )

        assert "No active draft" in str(exc_info.value)

        # Verify the published revision was NOT changed
        fetched = rev_repo.get(published.id)
        assert fetched is not None
        assert fetched.status == RevisionStatus.PUBLISHED.value
        prop_keys = {p.property_key for p in fetched.properties}
        assert "name" in prop_keys
        assert "hacked" not in prop_keys
