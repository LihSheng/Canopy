"""Unit tests for computed property syntax validation (Step 3)."""

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


class TestFormulaSyntaxValidation:
    """TDD: RED tests for syntax validation blocking draft save."""

    def _setup_entity(self, db_session, tenant_id):
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_id,
                object_type_key="syntax_test",
                display_name="Syntax Test",
                description="Syntax",
                created_at=datetime.now(UTC),
            )
        )
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_id,
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
            lock_holder_id="user-1",
        )
        return entity_id, service

    def test_empty_formula_blocks_add(self, db_session, tenant_context):
        """Empty formula is rejected at draft save."""
        entity_id, service = self._setup_entity(db_session, tenant_context.tenant_id)
        cp = ComputedProperty(
            id=str(uuid.uuid4()),
            property_key="total",
            display_name="Total",
            formula="",
            formula_type="arithmetic",
            output_type="number",
        )
        with pytest.raises(ValidationError) as exc:
            service.add_computed_property(entity_id, tenant_context.tenant_id, cp, lock_holder_id="user-1")
        assert "empty" in str(exc.value).lower()

    def test_unknown_function_blocks_add(self, db_session, tenant_context):
        """Unknown function is rejected at draft save."""
        entity_id, service = self._setup_entity(db_session, tenant_context.tenant_id)
        cp = ComputedProperty(
            id=str(uuid.uuid4()),
            property_key="total",
            display_name="Total",
            formula="foobar(salary)",
            formula_type="arithmetic",
            output_type="number",
        )
        with pytest.raises(ValidationError) as exc:
            service.add_computed_property(entity_id, tenant_context.tenant_id, cp, lock_holder_id="user-1")
        assert "unknown" in str(exc.value).lower() or "function" in str(exc.value).lower()

    def test_unbalanced_parentheses_blocks_add(self, db_session, tenant_context):
        """Unbalanced parentheses are rejected at draft save."""
        entity_id, service = self._setup_entity(db_session, tenant_context.tenant_id)
        cp = ComputedProperty(
            id=str(uuid.uuid4()),
            property_key="total",
            display_name="Total",
            formula="upper(salary",
            formula_type="arithmetic",
            output_type="string",
        )
        with pytest.raises(ValidationError) as exc:
            service.add_computed_property(entity_id, tenant_context.tenant_id, cp, lock_holder_id="user-1")
        assert "parenthes" in str(exc.value).lower() or "expected ')'" in str(exc.value).lower()

    def test_nonexistent_property_reference_blocks_add(self, db_session, tenant_context):
        """Reference to a property that does not exist in the entity is rejected."""
        entity_id, service = self._setup_entity(db_session, tenant_context.tenant_id)
        cp = ComputedProperty(
            id=str(uuid.uuid4()),
            property_key="total",
            display_name="Total",
            formula="add(salary, nonexistent)",
            formula_type="arithmetic",
            output_type="number",
        )
        with pytest.raises(ValidationError) as exc:
            service.add_computed_property(entity_id, tenant_context.tenant_id, cp, lock_holder_id="user-1")
        assert "nonexistent" in str(exc.value).lower()

    def test_cross_entity_reference_blocks_add(self, db_session, tenant_context):
        """Cross-entity reference (dot notation) is rejected."""
        entity_id, service = self._setup_entity(db_session, tenant_context.tenant_id)
        cp = ComputedProperty(
            id=str(uuid.uuid4()),
            property_key="total",
            display_name="Total",
            formula="other.salary",
            formula_type="arithmetic",
            output_type="number",
        )
        with pytest.raises(ValidationError) as exc:
            service.add_computed_property(entity_id, tenant_context.tenant_id, cp, lock_holder_id="user-1")
        assert (
            "cross" in str(exc.value).lower() or "entity" in str(exc.value).lower() or "dot" in str(exc.value).lower()
        )

    def test_valid_formula_passes(self, db_session, tenant_context):
        """Valid formula referencing existing properties is accepted."""
        entity_id, service = self._setup_entity(db_session, tenant_context.tenant_id)
        cp = ComputedProperty(
            id=str(uuid.uuid4()),
            property_key="total",
            display_name="Total",
            formula="add(salary, bonus)",
            formula_type="arithmetic",
            output_type="number",
        )
        draft = service.add_computed_property(entity_id, tenant_context.tenant_id, cp, lock_holder_id="user-1")
        assert len(draft.computed_properties) == 1
