"""Pure validation functions for semantic mapping.

These functions have no I/O side effects and are fully testable.
"""

from semantic.domain import PropertyMapping, SchemaColumn


def validate_pk_sample(column_values: list) -> list[dict]:
    """Validate primary key sample data for nulls and duplicates.

    This is a pure function that takes a list of column values (from
    a sample) and checks for obvious PK quality issues.

    Returns a list of error dicts.
    """
    errors: list[dict] = []
    seen: set = set()
    null_count = 0

    for i, val in enumerate(column_values):
        if val is None:
            null_count += 1
        else:
            normalized = str(val).strip().lower()
            if normalized in seen:
                errors.append(
                    {
                        "field": "primary_key",
                        "value": str(val),
                        "message": f"Duplicate primary key value found in sample row {i + 1}: '{val}'",
                    }
                )
            seen.add(normalized)

    if null_count > 0:
        errors.append(
            {
                "field": "primary_key",
                "value": None,
                "message": f"Primary key column contains {null_count} null value(s) in sample",
            }
        )

    return errors


def validate_property_names(properties: list[PropertyMapping]) -> list[dict]:
    """Validate property names for uniqueness (case-insensitive, whitespace-insensitive).

    Only included properties are validated — excluded properties are skipped.
    Returns a list of error dicts with field-level context.
    Each error: {"field": "property_name", "value": str, "message": str}
    """
    errors: list[dict] = []
    normalized: dict[str, list[int]] = {}  # normalized -> list of indices

    for i, prop in enumerate(properties):
        if not prop.included:
            continue  # skip excluded columns
        norm = prop.property_name.strip().lower()
        if not norm:
            errors.append(
                {
                    "field": f"properties[{i}].property_name",
                    "value": prop.property_name,
                    "message": "Property name must not be empty",
                }
            )
            continue
        if norm not in normalized:
            normalized[norm] = []
        normalized[norm].append(i)

    for norm, indices in normalized.items():
        if len(indices) > 1:
            for idx in indices:
                errors.append(
                    {
                        "field": f"properties[{idx}].property_name",
                        "value": properties[idx].property_name,
                        "message": f"Duplicate property name (after normalization): '{properties[idx].property_name}'",
                    }
                )

    return errors


def validate_primary_key(properties: list[PropertyMapping]) -> list[dict]:
    """Validate that exactly one primary key is selected and it is included."""
    errors: list[dict] = []
    pk_count = 0

    for i, prop in enumerate(properties):
        if prop.is_primary_key:
            pk_count += 1
            if not prop.included:
                errors.append(
                    {
                        "field": f"properties[{i}].included",
                        "value": prop.property_name,
                        "message": "Primary key column must be included in the mapping",
                    }
                )

    if pk_count == 0:
        errors.append(
            {
                "field": "primary_key",
                "value": None,
                "message": "A primary key must be selected",
            }
        )

    if pk_count > 1:
        errors.append(
            {
                "field": "primary_key",
                "value": None,
                "message": "Only one primary key can be selected",
            }
        )

    return errors


def validate_columns_exist(
    properties: list[PropertyMapping],
    schema_columns: list[SchemaColumn],
) -> list[dict]:
    """Validate that all source columns exist in the schema."""
    errors: list[dict] = []
    schema_names = {c.column_name for c in schema_columns}

    for i, prop in enumerate(properties):
        if prop.source_column not in schema_names:
            errors.append(
                {
                    "field": f"properties[{i}].source_column",
                    "value": prop.source_column,
                    "message": f"Column '{prop.source_column}' does not exist in the dataset schema",
                }
            )

    return errors


def validate_semantic_types(properties: list[PropertyMapping]) -> list[dict]:
    """Validate semantic types are from allowed set."""
    allowed = {"string", "integer", "number", "boolean", "datetime", "date"}
    errors: list[dict] = []

    for i, prop in enumerate(properties):
        if prop.semantic_type and prop.semantic_type not in allowed:
            errors.append(
                {
                    "field": f"properties[{i}].semantic_type",
                    "value": prop.semantic_type,
                    "message": f"Invalid semantic type '{prop.semantic_type}'. Allowed: {', '.join(sorted(allowed))}",
                }
            )

    return errors


def validate_mapping(
    properties: list[PropertyMapping],
    schema_columns: list[SchemaColumn] | None = None,
) -> list[dict]:
    """Run all validation rules and return combined errors."""
    errors: list[dict] = []
    errors.extend(validate_property_names(properties))
    errors.extend(validate_primary_key(properties))
    errors.extend(validate_semantic_types(properties))
    if schema_columns is not None:
        errors.extend(validate_columns_exist(properties, schema_columns))
    return errors
