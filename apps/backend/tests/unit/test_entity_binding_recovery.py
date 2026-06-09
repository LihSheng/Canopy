"""Unit tests for binding recovery mapping (Issue 3)."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from entity_revision.domain import EntityProperty, EntityRevision, RevisionStatus, SourceBinding
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


class TestBindingRecoveryService:
    def test_suggests_mapping_by_property_key_match(self, db_session, tenant_context):
        """When source field is missing, suggest a field matching the property_key."""
        from entity_revision.recovery_service import BindingRecoveryService

        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="recover_test",
                display_name="Recovery Test",
                description="Recovery",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        draft = rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=entity_id,
                revision_number=1,
                status=RevisionStatus.DRAFT.value,
                properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
                source_bindings=[
                    SourceBinding(
                        property_key="name", source_node_id="sn1", source_field_name="old_name", is_active=True
                    )
                ],
                source_nodes=[
                    {
                        "source_id": "sn1",
                        "source_type": "table",
                        "name": "t1",
                        "reference_id": "r1",
                        "fields": ["name", "email"],
                    }
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

        recovery = BindingRecoveryService(rev_repo)
        suggestions = recovery.get_recovery_suggestions(entity_id, draft.id)

        assert "sn1" in suggestions
        # old_name is missing; property_key "name" exists in fields
        assert suggestions["sn1"]["old_name"]["suggested_field"] == "name"
        assert suggestions["sn1"]["old_name"]["confidence"] == "high"

    def test_marks_needs_manual_when_no_match(self, db_session, tenant_context):
        """When no matching field exists, mark as needs_manual_mapping."""
        from entity_revision.recovery_service import BindingRecoveryService

        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="recover_manual",
                display_name="Recovery Manual",
                description="Recovery",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        draft = rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=entity_id,
                revision_number=1,
                status=RevisionStatus.DRAFT.value,
                properties=[EntityProperty(property_id="p1", property_key="missing", display_name="Missing")],
                source_bindings=[
                    SourceBinding(
                        property_key="missing", source_node_id="sn1", source_field_name="missing_field", is_active=True
                    )
                ],
                source_nodes=[
                    {
                        "source_id": "sn1",
                        "source_type": "table",
                        "name": "t1",
                        "reference_id": "r1",
                        "fields": ["name", "email"],
                    }
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

        recovery = BindingRecoveryService(rev_repo)
        suggestions = recovery.get_recovery_suggestions(entity_id, draft.id)

        assert "sn1" in suggestions
        assert suggestions["sn1"]["missing_field"]["suggested_field"] is None
        assert suggestions["sn1"]["missing_field"]["confidence"] == "manual"

    def test_apply_recovery_updates_bindings(self, db_session, tenant_context):
        """Applying recovery suggestions updates the draft bindings."""
        from entity_revision.recovery_service import BindingRecoveryService

        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="recover_apply",
                display_name="Recovery Apply",
                description="Recovery",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        draft = rev_repo.save(
            EntityRevision(
                id=str(uuid.uuid4()),
                entity_id=entity_id,
                revision_number=1,
                status=RevisionStatus.DRAFT.value,
                properties=[EntityProperty(property_id="p1", property_key="name", display_name="Name")],
                source_bindings=[
                    SourceBinding(
                        property_key="name", source_node_id="sn1", source_field_name="old_name", is_active=True
                    )
                ],
                source_nodes=[
                    {
                        "source_id": "sn1",
                        "source_type": "table",
                        "name": "t1",
                        "reference_id": "r1",
                        "fields": ["name", "email"],
                    }
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

        recovery = BindingRecoveryService(rev_repo)
        mapping = {"sn1": {"old_name": "name"}}
        updated_draft = recovery.apply_recovery(entity_id, draft.id, mapping)

        assert updated_draft.source_bindings[0].source_field_name == "name"
        assert updated_draft.updated_at > draft.updated_at
