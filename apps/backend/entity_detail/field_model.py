"""Unified field model for entity detail.

Provides a single view over both base properties and computed properties so that
the API can render them as first-class fields with visual grouping.
"""

from dataclasses import dataclass, field

from entity_revision.domain import ComputedProperty, EntityProperty


@dataclass
class EntityField:
    """Unified view of a base property or a computed property."""

    field_id: str
    field_kind: str  # "base" | "computed"
    property_key: str
    display_name: str
    semantic_type: str
    is_required: bool
    is_primary_key: bool
    sort_order: int
    formula: str | None = None
    formula_type: str | None = None
    is_active: bool = True

    @classmethod
    def from_base(cls, p: EntityProperty) -> "EntityField":
        return cls(
            field_id=p.property_id,
            field_kind="base",
            property_key=p.property_key,
            display_name=p.display_name,
            semantic_type=p.semantic_type,
            is_required=p.is_required,
            is_primary_key=p.is_primary_key,
            sort_order=p.sort_order,
            formula=None,
            formula_type=None,
            is_active=True,
        )

    @classmethod
    def from_computed(cls, cp: ComputedProperty) -> "EntityField":
        return cls(
            field_id=cp.id,
            field_kind="computed",
            property_key=cp.property_key,
            display_name=cp.display_name,
            semantic_type=cp.output_type,
            is_required=False,
            is_primary_key=False,
            sort_order=cp.sort_order,
            formula=cp.formula,
            formula_type=cp.formula_type,
            is_active=cp.is_active,
        )


@dataclass
class FieldGroup:
    """A named group of fields of a single kind."""

    group_name: str
    field_kind: str
    fields: list[EntityField] = field(default_factory=list)

    @classmethod
    def group_fields(cls, fields: list[EntityField]) -> list["FieldGroup"]:
        """Split fields into two groups: base first, then computed."""
        base_fields = sorted([f for f in fields if f.field_kind == "base"], key=lambda f: f.sort_order)
        computed_fields = sorted([f for f in fields if f.field_kind == "computed"], key=lambda f: f.sort_order)
        groups: list[FieldGroup] = []
        if base_fields:
            groups.append(cls(group_name="Base Properties", field_kind="base", fields=base_fields))
        if computed_fields:
            groups.append(
                cls(
                    group_name="Computed Properties",
                    field_kind="computed",
                    fields=computed_fields,
                )
            )
        return groups


class FieldUnifier:
    """Merge base and computed properties into a unified field model."""

    @staticmethod
    def unify_fields(
        base_properties: list[EntityProperty],
        computed_properties: list[ComputedProperty],
    ) -> list[EntityField]:
        """Return a single list of EntityField sorted by sort_order.

        Base properties come before computed properties at the same sort_order.
        """
        base_fields = [EntityField.from_base(p) for p in base_properties]
        computed_fields = [EntityField.from_computed(cp) for cp in computed_properties]
        all_fields = base_fields + computed_fields
        return sorted(all_fields, key=lambda f: (f.sort_order, f.field_kind == "computed"))

    @staticmethod
    def group_fields(
        base_properties: list[EntityProperty],
        computed_properties: list[ComputedProperty],
    ) -> list[FieldGroup]:
        """Return fields grouped by kind, each group sorted by sort_order."""
        base_fields = sorted(
            [EntityField.from_base(p) for p in base_properties],
            key=lambda f: f.sort_order,
        )
        computed_fields = sorted(
            [EntityField.from_computed(cp) for cp in computed_properties],
            key=lambda f: f.sort_order,
        )
        groups: list[FieldGroup] = []
        if base_fields:
            groups.append(FieldGroup(group_name="Base Properties", field_kind="base", fields=base_fields))
        if computed_fields:
            groups.append(
                FieldGroup(
                    group_name="Computed Properties",
                    field_kind="computed",
                    fields=computed_fields,
                )
            )
        return groups
