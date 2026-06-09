"""Unit tests for entity deprecation workflow."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from entity_revision.deprecation_service import EntityDeprecationService
from entity_revision.domain import EntityProperty, EntityRevision, RevisionStatus
from entity_revision.repository import EntityRevisionRepository
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


class TestEntityDeprecation:
    def test_deprecate_entity_sets_status(self, db_session, tenant_context):
        """Deprecating an entity sets its status to 'deprecated'."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        entity = obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="deprecate_test",
                display_name="Deprecation Test Entity",
                description="Testing deprecation",
                status="published",
                created_at=datetime.now(UTC),
            )
        )
        assert entity.status == "published"

        service = EntityDeprecationService(obj_repo)
        result = service.deprecate_entity(entity_id, tenant_context.tenant_id)

        assert result.status == "deprecated"

        fresh = obj_repo.get(entity_id, tenant_context.tenant_id)
        assert fresh is not None
        assert fresh.status == "deprecated"

    def test_deprecate_nonexistent_entity_raises(self, db_session, tenant_context):
        """Deprecating a nonexistent entity raises error."""
        obj_repo = ObjectTypeRepository(db_session)
        service = EntityDeprecationService(obj_repo)

        with pytest.raises(Exception) as exc_info:
            service.deprecate_entity("nonexistent", tenant_context.tenant_id)

        assert "not found" in str(exc_info.value).lower()

    def test_deprecated_entity_still_has_published_revision(self, db_session, tenant_context):
        """A deprecated entity's published revision remains accessible."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="deprec_rev_test",
                display_name="Deprecation + Revision Test",
                description="Entity with revision, then deprecated",
                status="published",
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
                source_bindings=[],
                links=[],
                source_nodes=[],
                computed_properties=[],
                layout_state={},
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                published_at=datetime.now(UTC),
            )
        )

        # Deprecate the entity
        service = EntityDeprecationService(obj_repo)
        service.deprecate_entity(entity_id, tenant_context.tenant_id)

        # Published revision should still be fetchable
        fetched = rev_repo.get_published(entity_id)
        assert fetched is not None
        assert fetched.status == RevisionStatus.PUBLISHED.value
        assert fetched.revision_number == 1

        # Entity status should be deprecated
        fresh_entity = obj_repo.get(entity_id, tenant_context.tenant_id)
        assert fresh_entity.status == "deprecated"

    def test_deprecate_entity_does_not_affect_other_entities(self, db_session, tenant_context):
        """Deprecating one entity does not affect another entity's status."""
        obj_repo = ObjectTypeRepository(db_session)

        e1 = obj_repo.save(
            ObjectType(
                id=str(uuid.uuid4()),
                tenant_id=tenant_context.tenant_id,
                object_type_key="entity_a",
                display_name="Entity A",
                description="...",
                status="published",
                created_at=datetime.now(UTC),
            )
        )
        e2 = obj_repo.save(
            ObjectType(
                id=str(uuid.uuid4()),
                tenant_id=tenant_context.tenant_id,
                object_type_key="entity_b",
                display_name="Entity B",
                description="...",
                status="published",
                created_at=datetime.now(UTC),
            )
        )

        service = EntityDeprecationService(obj_repo)
        service.deprecate_entity(e1.id, tenant_context.tenant_id)

        assert obj_repo.get(e1.id, tenant_context.tenant_id).status == "deprecated"
        assert obj_repo.get(e2.id, tenant_context.tenant_id).status == "published"
