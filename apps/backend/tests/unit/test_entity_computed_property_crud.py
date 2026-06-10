"""Unit tests for computed property CRUD (Issue 3)."""

import uuid
from datetime import UTC, datetime

import pytest

from context.tenant_context import TenantContext, set_current_tenant_context
from entity_revision.domain import (
    ComputedProperty,
    EntityProperty,
    SourceBinding,
)
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


class TestComputedPropertyCrud:
    def test_add_computed_property_to_draft(self, db_session, tenant_context):
        """Computed property can be added to a draft."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="computed_test",
                display_name="Computed Test",
                description="Computed",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[SourceBinding(property_key="salary", source_node_id="sn1", source_field_name="salary")],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            lock_holder_id="user-1",
        )

        cp = ComputedProperty(
            id=str(uuid.uuid4()),
            property_key="total_comp",
            display_name="Total Compensation",
            formula="multiply(salary, 1.1)",
            formula_type="arithmetic",
            inputs=["salary"],
            output_type="number",
            sort_order=1,
            is_active=True,
        )

        draft = service.add_computed_property(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            prop=cp,
            lock_holder_id="user-1",
        )

        assert len(draft.computed_properties) == 1
        assert draft.computed_properties[0].property_key == "total_comp"

    def test_update_computed_property_formula(self, db_session, tenant_context):
        """Computed property formula can be updated."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="computed_update",
                display_name="Computed Update",
                description="Computed",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[SourceBinding(property_key="salary", source_node_id="sn1", source_field_name="salary")],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total_comp",
                    display_name="Total Compensation",
                    formula="multiply(salary, 1.1)",
                    formula_type="arithmetic",
                    inputs=["salary"],
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            lock_holder_id="user-1",
        )

        draft = service.update_computed_property(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            computed_property_id="cp1",
            updates={"formula": "multiply(salary, 1.2)", "inputs": ["salary"]},
            lock_holder_id="user-1",
        )

        assert draft.computed_properties[0].formula == "multiply(salary, 1.2)"

    def test_remove_computed_property(self, db_session, tenant_context):
        """Computed property can be removed from draft."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="computed_remove",
                display_name="Computed Remove",
                description="Computed",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[SourceBinding(property_key="salary", source_node_id="sn1", source_field_name="salary")],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total_comp",
                    display_name="Total Compensation",
                    formula="multiply(salary, 1.1)",
                    formula_type="arithmetic",
                    inputs=["salary"],
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            lock_holder_id="user-1",
        )

        draft = service.remove_computed_property(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            computed_property_id="cp1",
            lock_holder_id="user-1",
        )

        assert len(draft.computed_properties) == 0

    def test_computed_property_references_valid_property_keys(self, db_session, tenant_context):
        """Draft accepts computed property with invalid refs; publish blocks it."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="computed_invalid",
                display_name="Computed Invalid",
                description="Computed",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[SourceBinding(property_key="salary", source_node_id="sn1", source_field_name="salary")],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            lock_holder_id="user-1",
        )

        cp = ComputedProperty(
            id=str(uuid.uuid4()),
            property_key="bad",
            display_name="Bad",
            formula="add(nonexistent, 1)",
            formula_type="arithmetic",
            inputs=["nonexistent"],
            output_type="number",
            sort_order=1,
            is_active=True,
        )

        # Draft save accepts invalid computed property (draft/publish safety pattern)
        draft = service.add_computed_property(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            prop=cp,
            lock_holder_id="user-1",
        )
        assert len(draft.computed_properties) == 1

        # Publish blocks it
        with pytest.raises(Exception) as exc_info:
            service.publish_draft(
                entity_id=entity_id,
                tenant_id=tenant_context.tenant_id,
            )
        error_msg = str(exc_info.value).lower()
        assert "nonexistent" in error_msg or "unknown" in error_msg or "publish validation failed" in error_msg

    def test_computed_property_preserved_through_publish(self, db_session, tenant_context):
        """Computed property survives publish."""
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_context.tenant_id,
                object_type_key="computed_publish",
                display_name="Computed Publish",
                description="Computed",
                created_at=datetime.now(UTC),
            )
        )

        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)

        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[EntityProperty(property_id="p1", property_key="salary", display_name="Salary")],
            source_bindings=[SourceBinding(property_key="salary", source_node_id="sn1", source_field_name="salary")],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total_comp",
                    display_name="Total Compensation",
                    formula="multiply(salary, 1.1)",
                    formula_type="arithmetic",
                    inputs=["salary"],
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            lock_holder_id="user-1",
            publish=True,
        )

        published = service.get_latest_published_entity(entity_id, tenant_context.tenant_id)
        assert len(published.computed_properties) == 1
        assert published.computed_properties[0].property_key == "total_comp"
