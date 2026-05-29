"""Pure validation functions for semantic mapping.

These functions have no I/O side effects and are fully testable.
"""

from semantic.domain import EntityLink, PropertyMapping, SchemaColumn


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


# ─── Entity Link Validation ───


def _normalize(s: str) -> str:
    """Trim and case-fold for duplicate comparison."""
    return s.strip().lower()


def validate_link_ids(links: list[EntityLink]) -> list[dict]:
    """Validate link_id: required, non-empty, no duplicates (trim+casefold)."""
    errors: list[dict] = []
    seen: dict[str, int] = {}  # normalized -> first index

    for i, link in enumerate(links):
        norm = _normalize(link.link_id)
        if not norm:
            errors.append(
                {
                    "field": f"links[{i}].link_id",
                    "value": link.link_id,
                    "message": "Link ID must not be empty",
                }
            )
            continue
        if norm in seen:
            errors.append(
                {
                    "field": f"links[{i}].link_id",
                    "value": link.link_id,
                    "message": f"Duplicate link_id: '{link.link_id}' matches '{links[seen[norm]].link_id}'",
                }
            )
        else:
            seen[norm] = i

    return errors


def validate_link_required_fields(links: list[EntityLink]) -> list[dict]:
    """Validate display_name is non-empty."""
    errors: list[dict] = []
    for i, link in enumerate(links):
        if not link.display_name or not link.display_name.strip():
            errors.append(
                {
                    "field": f"links[{i}].display_name",
                    "value": link.display_name,
                    "message": "Display name must not be empty",
                }
            )
    return errors


def validate_link_duplicate_edges(links: list[EntityLink]) -> list[dict]:
    """Validate no duplicate (source_property_key, target_object_type_id) pairs."""
    errors: list[dict] = []
    seen: dict[tuple[str, str], int] = {}

    for i, link in enumerate(links):
        key = (_normalize(link.source_property_key), _normalize(link.target_object_type_id))
        if key in seen:
            errors.append(
                {
                    "field": f"links[{i}].source_property_key",
                    "value": link.source_property_key,
                    "message": (
                        f"Duplicate edge: source property '{link.source_property_key}' "
                        f"already links to target object type '{link.target_object_type_id}'"
                    ),
                }
            )
        else:
            seen[key] = i

    return errors


def validate_link_excluded_properties(
    links: list[EntityLink],
    properties: list[PropertyMapping],
) -> list[dict]:
    """Validate source_property_key is not an excluded property."""
    errors: list[dict] = []
    prop_map: dict[str, PropertyMapping] = {}
    for p in properties:
        prop_map[p.property_name] = p

    for i, link in enumerate(links):
        prop = prop_map.get(link.source_property_key)
        if prop is not None and not prop.included:
            errors.append(
                {
                    "field": f"links[{i}].source_property_key",
                    "value": link.source_property_key,
                    "message": f"Cannot link from excluded property '{link.source_property_key}'",
                }
            )
        elif prop is None:
            errors.append(
                {
                    "field": f"links[{i}].source_property_key",
                    "value": link.source_property_key,
                    "message": f"Source property '{link.source_property_key}' not found in mapping properties",
                }
            )

    return errors


def validate_link_cardinality(links: list[EntityLink]) -> list[dict]:
    """Validate cardinality is an allowed value."""
    allowed = {"many_to_one", "many_to_many"}
    errors: list[dict] = []

    for i, link in enumerate(links):
        if link.cardinality not in allowed:
            errors.append(
                {
                    "field": f"links[{i}].cardinality",
                    "value": link.cardinality,
                    "message": f"Invalid cardinality '{link.cardinality}'. Allowed: {', '.join(sorted(allowed))}",
                }
            )

    return errors


def validate_links(
    links: list[EntityLink],
    properties: list[PropertyMapping],
) -> list[dict]:
    """Run all stateless link validation rules and return combined errors."""
    errors: list[dict] = []
    errors.extend(validate_link_ids(links))
    errors.extend(validate_link_required_fields(links))
    errors.extend(validate_link_duplicate_edges(links))
    errors.extend(validate_link_excluded_properties(links, properties))
    errors.extend(validate_link_cardinality(links))
    return errors
