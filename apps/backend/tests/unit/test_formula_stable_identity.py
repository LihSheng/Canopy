"""Unit tests for stable field identity (Step 7)."""

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


class TestFormulaStableIdentity:
    """TDD: RED tests for stable field identity."""

    def _setup_entity(self, db_session, tenant_id):
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_id,
                object_type_key="identity_test",
                display_name="Identity Test",
                description="Identity",
                created_at=datetime.now(UTC),
            )
        )
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        return entity_id, service

    def test_display_name_rename_does_not_break_formula(self, db_session, tenant_context):
        """Renaming display_name keeps property_key stable; formula still works."""
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
                )
            ],
            lock_holder_id="user-1",
            publish=True,
        )
        # Fork draft, rename display_name only
        service.fork_draft(entity_id, lock_holder_id="user-1", tenant_id=tenant_context.tenant_id)
        service.update_property(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            property_id="p1",
            updates={"display_name": "Annual Salary"},
            lock_holder_id="user-1",
        )
        # Publish should succeed because property_key is unchanged
        published = service.publish_draft(entity_id, tenant_context.tenant_id)
        assert published.status == "published"
        # Ensure property_id survived
        prop = next(p for p in published.properties if p.property_id == "p1")
        assert prop.display_name == "Annual Salary"
        assert prop.property_key == "salary"

    def test_property_key_change_requires_formula_update(self, db_session, tenant_context):
        """Changing property_key breaks computed property references."""
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
                )
            ],
            lock_holder_id="user-1",
            publish=True,
        )
        # Fork draft, change property_key
        service.fork_draft(entity_id, lock_holder_id="user-1", tenant_id=tenant_context.tenant_id)
        service.update_property(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            property_id="p1",
            updates={"property_key": "annual_salary"},
            lock_holder_id="user-1",
        )
        # Warnings should mention the broken reference
        warnings = service.get_computed_property_warnings(entity_id)
        assert any("salary" in w for w in warnings)
        # Publish should fail
        with pytest.raises(ValidationError) as exc:
            service.publish_draft(entity_id, tenant_context.tenant_id)
        assert "salary" in str(exc.value).lower()

    def test_property_id_preserved_through_renames(self, db_session, tenant_context):
        """property_id stays immutable even when property_key and display_name change."""
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
            lock_holder_id="user-1",
        )
        draft = service.update_property(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            property_id="p1",
            updates={"property_key": "annual_salary", "display_name": "Annual Salary"},
            lock_holder_id="user-1",
        )
        prop = next(p for p in draft.properties if p.property_id == "p1")
        assert prop.property_key == "annual_salary"
        assert prop.display_name == "Annual Salary"
        assert prop.property_id == "p1"

    def test_formula_engine_uses_property_key(self, db_session, tenant_context):
        """Engine resolves values by property_key, not property_id."""
        from entity_formula_engine.engine import FormulaEngine

        engine = FormulaEngine()
        result = engine.evaluate(
            formula="multiply(salary, 2)",
            inputs=["salary"],
            row_data={"salary": 1000},
        )
        assert result == 2000

    def test_check_computed_property_dependencies(self, db_session, tenant_context):
        """_check_computed_property_dependencies flags broken references after rename."""
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
                )
            ],
            lock_holder_id="user-1",
        )
        # Rename property_key
        draft = service.update_property(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            property_id="p1",
            updates={"property_key": "annual_salary"},
            lock_holder_id="user-1",
        )
        warnings = service._check_computed_property_dependencies(draft)
        assert any("salary" in w for w in warnings)
