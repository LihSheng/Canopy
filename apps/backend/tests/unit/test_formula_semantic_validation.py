"""Unit tests for computed property semantic validation at publish (Step 5)."""

import uuid
from datetime import UTC, datetime

import pytest

from common.errors import ValidationError
from entity_revision.domain import ComputedProperty, EntityProperty, SourceBinding
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


class TestFormulaSemanticValidation:
    """TDD: RED tests for semantic validation blocking publish."""

    def _setup_entity(self, db_session, tenant_id):
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_id,
                object_type_key="semantic_test",
                display_name="Semantic Test",
                description="Semantic",
                created_at=datetime.now(UTC),
            )
        )
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        return entity_id, service

    def test_publish_fails_on_removed_property_reference(self, db_session, tenant_context):
        """Publish fails if a computed property references a removed property."""
        entity_id, service = self._setup_entity(db_session, tenant_context.tenant_id)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[
                EntityProperty(property_id="p1", property_key="salary", display_name="Salary"),
                EntityProperty(property_id="p2", property_key="bonus", display_name="Bonus"),
            ],
            source_bindings=[
                SourceBinding(property_key="salary", source_node_id="sn1", source_field_name="salary"),
                SourceBinding(property_key="bonus", source_node_id="sn1", source_field_name="bonus"),
            ],
            source_nodes=[
                {
                    "source_id": "sn1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["salary", "bonus"],
                }
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total",
                    display_name="Total",
                    formula="add(salary, bonus)",
                    formula_type="arithmetic",
                    inputs=["salary", "bonus"],
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            publish=True,
        )
        # Fork draft, remove bonus property
        service.fork_draft(entity_id, lock_holder_id="user-1", tenant_id=tenant_context.tenant_id)
        # Remove bonus property from draft
        service.remove_property(entity_id, tenant_context.tenant_id, property_id="p2", lock_holder_id="user-1")
        # Attempt to publish
        with pytest.raises(ValidationError) as exc:
            service.publish_draft(entity_id, tenant_context.tenant_id)
        assert "bonus" in str(exc.value).lower()

    def test_publish_fails_on_circular_dependency(self, db_session, tenant_context):
        """Publish fails if a computed property references another computed property."""
        entity_id, service = self._setup_entity(db_session, tenant_context.tenant_id)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[
                EntityProperty(property_id="p1", property_key="salary", display_name="Salary"),
            ],
            source_bindings=[
                SourceBinding(property_key="salary", source_node_id="sn1", source_field_name="salary"),
            ],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["salary"]}
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="adjusted",
                    display_name="Adjusted",
                    formula="multiply(salary, 1.1)",
                    formula_type="arithmetic",
                    inputs=["salary"],
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                ),
                ComputedProperty(
                    id="cp2",
                    property_key="double_adjusted",
                    display_name="Double Adjusted",
                    formula="multiply(adjusted, 2)",
                    formula_type="arithmetic",
                    inputs=["adjusted"],
                    output_type="number",
                    sort_order=2,
                    is_active=True,
                ),
            ],
            lock_holder_id="user-1",
        )
        with pytest.raises(ValidationError) as exc:
            service.publish_draft(entity_id, tenant_context.tenant_id)
        assert "circular" in str(exc.value).lower() or "computed" in str(exc.value).lower()

    def test_publish_fails_on_output_type_mismatch(self, db_session, tenant_context):
        """Publish fails if formula output type does not match declared output_type."""
        entity_id, service = self._setup_entity(db_session, tenant_context.tenant_id)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[
                EntityProperty(property_id="p1", property_key="name", display_name="Name"),
            ],
            source_bindings=[
                SourceBinding(property_key="name", source_node_id="sn1", source_field_name="name"),
            ],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["name"]}
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="upper_name",
                    display_name="Upper Name",
                    formula="upper(name)",
                    formula_type="transform",
                    inputs=["name"],
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            lock_holder_id="user-1",
        )
        with pytest.raises(ValidationError) as exc:
            service.publish_draft(entity_id, tenant_context.tenant_id)
        assert "type" in str(exc.value).lower()

    def test_publish_succeeds_with_valid_formulas(self, db_session, tenant_context):
        """Publish succeeds when all computed properties are valid."""
        entity_id, service = self._setup_entity(db_session, tenant_context.tenant_id)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[
                EntityProperty(property_id="p1", property_key="salary", display_name="Salary"),
                EntityProperty(property_id="p2", property_key="bonus", display_name="Bonus"),
            ],
            source_bindings=[
                SourceBinding(property_key="salary", source_node_id="sn1", source_field_name="salary"),
                SourceBinding(property_key="bonus", source_node_id="sn1", source_field_name="bonus"),
            ],
            source_nodes=[
                {
                    "source_id": "sn1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["salary", "bonus"],
                }
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total",
                    display_name="Total",
                    formula="add(salary, bonus)",
                    formula_type="arithmetic",
                    inputs=["salary", "bonus"],
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            lock_holder_id="user-1",
            publish=True,
        )
        published = service.get_latest_published_entity(entity_id, tenant_context.tenant_id)
        assert published.status == "published"
        assert len(published.computed_properties) == 1

    def test_publish_fails_if_property_key_changed_and_old_key_referenced(self, db_session, tenant_context):
        """Publish fails if a computed property still references a renamed property key."""
        entity_id, service = self._setup_entity(db_session, tenant_context.tenant_id)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[
                EntityProperty(property_id="p1", property_key="salary", display_name="Salary"),
                EntityProperty(property_id="p2", property_key="bonus", display_name="Bonus"),
            ],
            source_bindings=[
                SourceBinding(property_key="salary", source_node_id="sn1", source_field_name="salary"),
                SourceBinding(property_key="bonus", source_node_id="sn1", source_field_name="bonus"),
            ],
            source_nodes=[
                {
                    "source_id": "sn1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["salary", "bonus"],
                }
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="total",
                    display_name="Total",
                    formula="add(salary, bonus)",
                    formula_type="arithmetic",
                    inputs=["salary", "bonus"],
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            publish=True,
        )
        # Fork draft, rename bonus -> annual_bonus
        service.fork_draft(entity_id, lock_holder_id="user-1", tenant_id=tenant_context.tenant_id)
        service.update_property(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            property_id="p2",
            updates={"property_key": "annual_bonus"},
            lock_holder_id="user-1",
        )
        # Attempt to publish
        with pytest.raises(ValidationError) as exc:
            service.publish_draft(entity_id, tenant_context.tenant_id)
        assert "bonus" in str(exc.value).lower() or "annual_bonus" in str(exc.value).lower()
