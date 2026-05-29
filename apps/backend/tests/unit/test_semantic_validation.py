"""Unit tests for semantic mapping validation (pure functions)."""

from semantic.domain import PropertyMapping, SchemaColumn
from semantic.validation import (
    validate_mapping,
    validate_pk_sample,
    validate_primary_key,
    validate_property_names,
    validate_semantic_types,
)


class TestValidatePropertyNames:
    def test_unique_names_pass(self):
        props = [
            PropertyMapping(source_column="a", property_name="Name", included=True),
            PropertyMapping(source_column="b", property_name="Email", included=True),
        ]
        errors = validate_property_names(props)
        assert errors == []

    def test_duplicate_names_blocked(self):
        props = [
            PropertyMapping(source_column="a", property_name="Name", included=True),
            PropertyMapping(source_column="b", property_name="name", included=True),
        ]
        errors = validate_property_names(props)
        assert len(errors) == 2
        assert all(e["field"].startswith("properties[") for e in errors)

    def test_whitespace_insensitive_dedup(self):
        props = [
            PropertyMapping(source_column="a", property_name="  Full Name  ", included=True),
            PropertyMapping(source_column="b", property_name="full name", included=True),
        ]
        errors = validate_property_names(props)
        assert len(errors) == 2

    def test_empty_name_blocked(self):
        props = [
            PropertyMapping(source_column="a", property_name="  ", included=True),
        ]
        errors = validate_property_names(props)
        assert len(errors) == 1
        assert "empty" in errors[0]["message"].lower()

    def test_excluded_properties_skipped(self):
        """Excluded columns should not trigger property-name validation."""
        props = [
            PropertyMapping(source_column="a", property_name="", included=False),
            PropertyMapping(source_column="b", property_name="  ", included=False),
        ]
        errors = validate_property_names(props)
        assert errors == []

    def test_excluded_does_not_cause_duplicate(self):
        """An excluded property with same name as an included one should not trigger duplicate."""
        props = [
            PropertyMapping(source_column="a", property_name="Name", included=True),
            PropertyMapping(source_column="b", property_name="name", included=False),
        ]
        errors = validate_property_names(props)
        assert errors == []


class TestValidatePrimaryKey:
    def test_pk_selected_and_included_passes(self):
        props = [
            PropertyMapping(source_column="id", property_name="ID", is_primary_key=True, included=True),
            PropertyMapping(source_column="name", property_name="Name", included=True),
        ]
        errors = validate_primary_key(props)
        assert errors == []

    def test_no_pk_selected_blocked(self):
        props = [
            PropertyMapping(source_column="name", property_name="Name", included=True),
        ]
        errors = validate_primary_key(props)
        assert len(errors) == 1
        assert "primary key must be selected" in errors[0]["message"].lower()

    def test_pk_excluded_blocked(self):
        props = [
            PropertyMapping(source_column="id", property_name="ID", is_primary_key=True, included=False),
        ]
        errors = validate_primary_key(props)
        assert len(errors) == 1
        assert "included" in errors[0]["message"].lower()

    def test_multiple_pk_blocked(self):
        props = [
            PropertyMapping(source_column="a", property_name="A", is_primary_key=True, included=True),
            PropertyMapping(source_column="b", property_name="B", is_primary_key=True, included=True),
        ]
        errors = validate_primary_key(props)
        assert len(errors) == 1
        assert "Only one" in errors[0]["message"]


class TestValidateSemanticTypes:
    def test_valid_types_pass(self):
        props = [
            PropertyMapping(source_column="a", property_name="A", semantic_type="string"),
            PropertyMapping(source_column="b", property_name="B", semantic_type="integer"),
            PropertyMapping(source_column="c", property_name="C", semantic_type="boolean"),
        ]
        errors = validate_semantic_types(props)
        assert errors == []

    def test_invalid_type_blocked(self):
        props = [
            PropertyMapping(source_column="a", property_name="A", semantic_type="blob"),
        ]
        errors = validate_semantic_types(props)
        assert len(errors) == 1


class TestValidateColumnsExist:
    def test_columns_exist_pass(self):
        schema = [SchemaColumn(column_name="id", primitive_type="string")]
        props = [
            PropertyMapping(source_column="id", property_name="ID"),
        ]
        from semantic.validation import validate_columns_exist

        errors = validate_columns_exist(props, schema)
        assert errors == []

    def test_missing_column_blocked(self):
        schema = [SchemaColumn(column_name="id", primitive_type="string")]
        props = [
            PropertyMapping(source_column="nonexistent", property_name="Bad"),
        ]
        from semantic.validation import validate_columns_exist

        errors = validate_columns_exist(props, schema)
        assert len(errors) == 1


class TestValidatePkSample:
    def test_no_nulls_passes(self):
        errors = validate_pk_sample([1, 2, 3, 4, 5])
        assert errors == []

    def test_nulls_blocked(self):
        errors = validate_pk_sample([1, None, 3])
        assert len(errors) == 1
        assert "null" in errors[0]["message"].lower()

    def test_duplicates_blocked(self):
        errors = validate_pk_sample([1, 2, 2, 3])
        assert len(errors) == 1
        assert "duplicate" in errors[0]["message"].lower()

    def test_nulls_and_duplicates_reported(self):
        errors = validate_pk_sample([None, 1, 1, None])
        # Should report null count + duplicates
        assert len(errors) >= 2

    def test_empty_sample_passes(self):
        errors = validate_pk_sample([])
        assert errors == []


class TestValidateMapping:
    def test_valid_mapping_passes(self):
        schema = [
            SchemaColumn(column_name="id", primitive_type="string"),
            SchemaColumn(column_name="name", primitive_type="string"),
        ]
        props = [
            PropertyMapping(source_column="id", property_name="ID", is_primary_key=True, included=True),
            PropertyMapping(source_column="name", property_name="Name", included=True),
        ]
        errors = validate_mapping(props, schema)
        assert errors == []

    def test_multiple_errors_reported(self):
        schema = [
            SchemaColumn(column_name="id", primitive_type="string"),
        ]
        props = [
            PropertyMapping(source_column="id", property_name="ID", is_primary_key=False, included=True),
            PropertyMapping(source_column="bad", property_name="Bad", included=True),
        ]
        errors = validate_mapping(props, schema)
        # Should report: no PK, missing column
        assert len(errors) >= 2

    def test_no_schema_skips_column_check(self):
        props = [
            PropertyMapping(source_column="id", property_name="ID", is_primary_key=True, included=True),
        ]
        errors = validate_mapping(props, schema_columns=None)
        assert errors == []
