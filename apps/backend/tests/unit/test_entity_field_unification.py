"""Unit tests for unified entity field model (Issue 6, Step 1).

Pure logic tests — no DB or framework required.
"""

import pytest

from entity_revision.domain import ComputedProperty, EntityProperty

pytestmark = pytest.mark.unit


class TestEntityFieldUnification:
    def test_entity_field_can_represent_base_property(self):
        """EntityField captures a base property with field_kind='base'."""
        from entity_detail.field_model import EntityField

        base = EntityProperty(
            property_id="p1",
            property_key="salary",
            display_name="Salary",
            semantic_type="number",
            is_required=True,
            is_primary_key=False,
            sort_order=1,
        )
        field = EntityField.from_base(base)
        assert field.field_kind == "base"
        assert field.field_id == "p1"
        assert field.property_key == "salary"
        assert field.display_name == "Salary"
        assert field.semantic_type == "number"
        assert field.is_required is True
        assert field.is_primary_key is False
        assert field.sort_order == 1
        assert field.formula is None
        assert field.formula_type is None
        assert field.is_active is True

    def test_entity_field_can_represent_computed_property(self):
        """EntityField captures a computed property with field_kind='computed'."""
        from entity_detail.field_model import EntityField

        computed = ComputedProperty(
            id="cp1",
            property_key="total_comp",
            display_name="Total Compensation",
            formula="salary * 1.1",
            formula_type="arithmetic",
            inputs=["salary"],
            output_type="number",
            sort_order=2,
            is_active=True,
        )
        field = EntityField.from_computed(computed)
        assert field.field_kind == "computed"
        assert field.field_id == "cp1"
        assert field.property_key == "total_comp"
        assert field.display_name == "Total Compensation"
        assert field.semantic_type == "number"
        assert field.is_required is False
        assert field.is_primary_key is False
        assert field.sort_order == 2
        assert field.formula == "salary * 1.1"
        assert field.formula_type == "arithmetic"
        assert field.is_active is True

    def test_sorting_by_sort_order_puts_base_before_computed(self):
        """Mixed fields sort by sort_order; base fields come before computed fields at same order."""
        from entity_detail.field_model import EntityField

        base = EntityField.from_base(
            EntityProperty(
                property_id="p1",
                property_key="salary",
                display_name="Salary",
                semantic_type="number",
                is_required=False,
                is_primary_key=False,
                sort_order=1,
            )
        )
        computed = EntityField.from_computed(
            ComputedProperty(
                id="cp1",
                property_key="total_comp",
                display_name="Total Compensation",
                formula="salary * 1.1",
                formula_type="arithmetic",
                inputs=["salary"],
                output_type="number",
                sort_order=1,
                is_active=True,
            )
        )
        fields = sorted([computed, base], key=lambda f: (f.sort_order, f.field_kind == "computed"))
        assert [f.field_kind for f in fields] == ["base", "computed"]

    def test_field_group_groups_by_kind(self):
        """FieldGroup groups fields by field_kind and preserves sort order within group."""
        from entity_detail.field_model import EntityField, FieldGroup

        base1 = EntityField.from_base(
            EntityProperty(
                property_id="p1",
                property_key="salary",
                display_name="Salary",
                semantic_type="number",
                is_required=False,
                is_primary_key=False,
                sort_order=2,
            )
        )
        base2 = EntityField.from_base(
            EntityProperty(
                property_id="p2",
                property_key="name",
                display_name="Name",
                semantic_type="string",
                is_required=False,
                is_primary_key=False,
                sort_order=1,
            )
        )
        computed1 = EntityField.from_computed(
            ComputedProperty(
                id="cp1",
                property_key="total_comp",
                display_name="Total Compensation",
                formula="salary * 1.1",
                formula_type="arithmetic",
                inputs=["salary"],
                output_type="number",
                sort_order=1,
                is_active=True,
            )
        )
        groups = FieldGroup.group_fields([base1, computed1, base2])
        assert len(groups) == 2
        assert groups[0].field_kind == "base"
        assert [f.property_key for f in groups[0].fields] == ["name", "salary"]
        assert groups[1].field_kind == "computed"
        assert [f.property_key for f in groups[1].fields] == ["total_comp"]

    def test_field_unifier_produces_sorted_fields(self):
        """FieldUnifier merges base and computed properties and returns sorted fields."""
        from entity_detail.field_model import FieldUnifier

        base_props = [
            EntityProperty(
                property_id="p1",
                property_key="salary",
                display_name="Salary",
                semantic_type="number",
                is_required=False,
                is_primary_key=False,
                sort_order=2,
            ),
            EntityProperty(
                property_id="p2",
                property_key="name",
                display_name="Name",
                semantic_type="string",
                is_required=False,
                is_primary_key=False,
                sort_order=1,
            ),
        ]
        computed_props = [
            ComputedProperty(
                id="cp1",
                property_key="total_comp",
                display_name="Total Compensation",
                formula="salary * 1.1",
                formula_type="arithmetic",
                inputs=["salary"],
                output_type="number",
                sort_order=1,
                is_active=True,
            ),
        ]
        fields = FieldUnifier.unify_fields(base_props, computed_props)
        assert [f.field_id for f in fields] == ["p2", "cp1", "p1"]
        assert [f.field_kind for f in fields] == ["base", "computed", "base"]

    def test_field_unifier_produces_groups(self):
        """FieldUnifier produces two groups: base and computed, each sorted."""
        from entity_detail.field_model import FieldUnifier

        base_props = [
            EntityProperty(
                property_id="p1",
                property_key="salary",
                display_name="Salary",
                semantic_type="number",
                is_required=False,
                is_primary_key=False,
                sort_order=2,
            ),
        ]
        computed_props = [
            ComputedProperty(
                id="cp1",
                property_key="total_comp",
                display_name="Total Compensation",
                formula="salary * 1.1",
                formula_type="arithmetic",
                inputs=["salary"],
                output_type="number",
                sort_order=1,
                is_active=True,
            ),
        ]
        groups = FieldUnifier.group_fields(base_props, computed_props)
        assert len(groups) == 2
        assert groups[0].group_name == "Base Properties"
        assert groups[0].field_kind == "base"
        assert groups[1].group_name == "Computed Properties"
        assert groups[1].field_kind == "computed"
        assert [f.field_id for f in groups[0].fields] == ["p1"]
        assert [f.field_id for f in groups[1].fields] == ["cp1"]
