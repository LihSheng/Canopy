"""Unit tests for computed property materialization (Step 9)."""

import uuid
from datetime import UTC, datetime

import pytest

from entity_materialization.repository import EntityMaterializationRepository
from entity_materialization.service import EntityMaterializationService
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


class TestFormulaMaterialization:
    """TDD: RED tests for computed property evaluation during materialization."""

    def _setup_entity(self, db_session, tenant_id):
        entity_id = str(uuid.uuid4())
        obj_repo = ObjectTypeRepository(db_session)
        obj_repo.save(
            ObjectType(
                id=entity_id,
                tenant_id=tenant_id,
                object_type_key="mat_test",
                display_name="Materialization Test",
                description="Materialization",
                created_at=datetime.now(UTC),
            )
        )
        rev_repo = EntityRevisionRepository(db_session)
        service = EntityRevisionService(rev_repo, obj_repo)
        return entity_id, rev_repo, service

    def _mock_source_reader(self, rows):
        def _read(source_node):
            return rows

        return _read

    def test_materialization_includes_computed_properties(self, db_session, tenant_context):
        """Materialized rows include computed property values."""
        entity_id, rev_repo, rev_service = self._setup_entity(db_session, tenant_context.tenant_id)
        revision = rev_service.create_initial_revision(
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
                    formula="multiply(salary, 2)",
                    formula_type="arithmetic",
                    inputs=["salary"],
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            publish=True,
        )

        mat_repo = EntityMaterializationRepository(db_session)
        mat_service = EntityMaterializationService(
            revision_repo=rev_repo,
            materialization_repo=mat_repo,
            source_data_reader=self._mock_source_reader([{"salary": 5000}]),
        )
        stats = mat_service.materialize_entity(entity_id, revision.id)
        assert stats["rows_inserted"] == 1

        rows = mat_service.get_rows(entity_id, revision.id)
        assert len(rows) == 1
        assert rows[0].row_data["salary"] == 5000
        assert rows[0].row_data["adjusted"] == 10000

    def test_failed_evaluation_produces_null(self, db_session, tenant_context):
        """If a computed property evaluation fails, the value is null."""
        entity_id, rev_repo, rev_service = self._setup_entity(db_session, tenant_context.tenant_id)
        revision = rev_service.create_initial_revision(
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
                    property_key="bad",
                    display_name="Bad",
                    formula="divide(salary, 0)",
                    formula_type="arithmetic",
                    inputs=["salary"],
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            publish=True,
        )

        mat_repo = EntityMaterializationRepository(db_session)
        mat_service = EntityMaterializationService(
            revision_repo=rev_repo,
            materialization_repo=mat_repo,
            source_data_reader=self._mock_source_reader([{"salary": 5000}]),
        )
        mat_service.materialize_entity(entity_id, revision.id)
        rows = mat_service.get_rows(entity_id, revision.id)
        assert len(rows) == 1
        assert rows[0].row_data["salary"] == 5000
        assert rows[0].row_data["bad"] is None

    def test_computed_properties_evaluated_after_base_properties(self, db_session, tenant_context):
        """Computed properties are added after base properties in the row."""
        entity_id, rev_repo, rev_service = self._setup_entity(db_session, tenant_context.tenant_id)
        revision = rev_service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[
                EntityProperty(property_id="p1", property_key="first_name", display_name="First Name"),
                EntityProperty(property_id="p2", property_key="last_name", display_name="Last Name"),
            ],
            source_bindings=[
                SourceBinding(property_key="first_name", source_node_id="sn1", source_field_name="first_name"),
                SourceBinding(property_key="last_name", source_node_id="sn1", source_field_name="last_name"),
            ],
            source_nodes=[
                {
                    "source_id": "sn1",
                    "source_type": "table",
                    "name": "t1",
                    "reference_id": "r1",
                    "fields": ["first_name", "last_name"],
                }
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="full_name",
                    display_name="Full Name",
                    formula="concat(first_name, ' ', last_name)",
                    formula_type="transform",
                    inputs=["first_name", "last_name"],
                    output_type="string",
                    sort_order=1,
                    is_active=True,
                )
            ],
            publish=True,
        )

        mat_repo = EntityMaterializationRepository(db_session)
        mat_service = EntityMaterializationService(
            revision_repo=rev_repo,
            materialization_repo=mat_repo,
            source_data_reader=self._mock_source_reader([{"first_name": "Alice", "last_name": "Smith"}]),
        )
        mat_service.materialize_entity(entity_id, revision.id)
        rows = mat_service.get_rows(entity_id, revision.id)
        assert len(rows) == 1
        assert rows[0].row_data["first_name"] == "Alice"
        assert rows[0].row_data["last_name"] == "Smith"
        assert rows[0].row_data["full_name"] == "Alice Smith"

    def test_materialized_rows_include_both_base_and_computed(self, db_session, tenant_context):
        """Row data contains both base properties and computed properties."""
        entity_id, rev_repo, rev_service = self._setup_entity(db_session, tenant_context.tenant_id)
        revision = rev_service.create_initial_revision(
            entity_id=entity_id,
            tenant_id=tenant_context.tenant_id,
            properties=[
                EntityProperty(property_id="p1", property_key="a", display_name="A"),
            ],
            source_bindings=[
                SourceBinding(property_key="a", source_node_id="sn1", source_field_name="a"),
            ],
            source_nodes=[
                {"source_id": "sn1", "source_type": "table", "name": "t1", "reference_id": "r1", "fields": ["a"]}
            ],
            computed_properties=[
                ComputedProperty(
                    id="cp1",
                    property_key="b",
                    display_name="B",
                    formula="add(a, 1)",
                    formula_type="arithmetic",
                    inputs=["a"],
                    output_type="number",
                    sort_order=1,
                    is_active=True,
                )
            ],
            publish=True,
        )

        mat_repo = EntityMaterializationRepository(db_session)
        mat_service = EntityMaterializationService(
            revision_repo=rev_repo,
            materialization_repo=mat_repo,
            source_data_reader=self._mock_source_reader([{"a": 10}]),
        )
        mat_service.materialize_entity(entity_id, revision.id)
        rows = mat_service.get_rows(entity_id, revision.id)
        assert len(rows) == 1
        assert "a" in rows[0].row_data
        assert "b" in rows[0].row_data
        assert rows[0].row_data["a"] == 10
        assert rows[0].row_data["b"] == 11
