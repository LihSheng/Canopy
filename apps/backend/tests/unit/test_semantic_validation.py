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


# ─── Entity Link Validation Tests ───


class TestValidateLinkIds:
    def test_unique_link_ids_pass(self):
        from semantic.domain import EntityLink
        from semantic.validation import validate_link_ids

        links = [
            EntityLink(
                link_id="reports_to",
                display_name="Reports To",
                source_property_key="mgr_id",
                target_object_type_id="obj_1",
                target_property_key="id",
            ),
            EntityLink(
                link_id="department",
                display_name="Department",
                source_property_key="dept_id",
                target_object_type_id="obj_2",
                target_property_key="id",
            ),
        ]
        errors = validate_link_ids(links)
        assert errors == []

    def test_duplicate_link_ids_blocked(self):
        from semantic.domain import EntityLink
        from semantic.validation import validate_link_ids

        links = [
            EntityLink(
                link_id="reports_to",
                display_name="Reports To",
                source_property_key="mgr_id",
                target_object_type_id="obj_1",
                target_property_key="id",
            ),
            EntityLink(
                link_id="Reports_To",
                display_name="Duplicate",
                source_property_key="other",
                target_object_type_id="obj_2",
                target_property_key="id",
            ),
        ]
        errors = validate_link_ids(links)
        assert len(errors) == 1
        assert "duplicate" in errors[0]["message"].lower()

    def test_empty_link_id_blocked(self):
        from semantic.domain import EntityLink
        from semantic.validation import validate_link_ids

        links = [
            EntityLink(
                link_id="  ",
                display_name="Empty",
                source_property_key="col",
                target_object_type_id="obj",
                target_property_key="id",
            ),
        ]
        errors = validate_link_ids(links)
        assert len(errors) == 1
        assert "empty" in errors[0]["message"].lower()

    def test_whitespace_casefold_dedup(self):
        from semantic.domain import EntityLink
        from semantic.validation import validate_link_ids

        links = [
            EntityLink(
                link_id="  Link_A  ",
                display_name="A",
                source_property_key="a",
                target_object_type_id="o1",
                target_property_key="id",
            ),
            EntityLink(
                link_id="link_a",
                display_name="B",
                source_property_key="b",
                target_object_type_id="o2",
                target_property_key="id",
            ),
        ]
        errors = validate_link_ids(links)
        assert len(errors) == 1
        assert "duplicate" in errors[0]["message"].lower()


class TestValidateLinkRequiredFields:
    def test_display_name_required(self):
        from semantic.domain import EntityLink
        from semantic.validation import validate_link_required_fields

        links = [
            EntityLink(
                link_id="ok",
                display_name="  ",
                source_property_key="col",
                target_object_type_id="obj",
                target_property_key="id",
            ),
        ]
        errors = validate_link_required_fields(links)
        assert len(errors) == 1
        assert "display name" in errors[0]["message"].lower()

    def test_valid_display_name_passes(self):
        from semantic.domain import EntityLink
        from semantic.validation import validate_link_required_fields

        links = [
            EntityLink(
                link_id="ok",
                display_name="Valid Name",
                source_property_key="col",
                target_object_type_id="obj",
                target_property_key="id",
            ),
        ]
        errors = validate_link_required_fields(links)
        assert errors == []


class TestValidateLinkDuplicateEdges:
    def test_duplicate_edge_blocked(self):
        from semantic.domain import EntityLink
        from semantic.validation import validate_link_duplicate_edges

        links = [
            EntityLink(
                link_id="a",
                display_name="A",
                source_property_key="dept_id",
                target_object_type_id="obj_department",
                target_property_key="id",
            ),
            EntityLink(
                link_id="b",
                display_name="B",
                source_property_key="dept_id",
                target_object_type_id="obj_department",
                target_property_key="id",
            ),
        ]
        errors = validate_link_duplicate_edges(links)
        assert len(errors) == 1
        assert "duplicate edge" in errors[0]["message"].lower()

    def test_different_edges_pass(self):
        from semantic.domain import EntityLink
        from semantic.validation import validate_link_duplicate_edges

        links = [
            EntityLink(
                link_id="a",
                display_name="A",
                source_property_key="dept_id",
                target_object_type_id="obj_department",
                target_property_key="id",
            ),
            EntityLink(
                link_id="b",
                display_name="B",
                source_property_key="mgr_id",
                target_object_type_id="obj_employee",
                target_property_key="id",
            ),
        ]
        errors = validate_link_duplicate_edges(links)
        assert errors == []


class TestValidateLinkExcludedProperties:
    def test_excluded_source_blocked(self):
        from semantic.domain import EntityLink, PropertyMapping
        from semantic.validation import validate_link_excluded_properties

        links = [
            EntityLink(
                link_id="a",
                display_name="A",
                source_property_key="internal_code",
                target_object_type_id="obj",
                target_property_key="id",
            ),
        ]
        properties = [
            PropertyMapping(source_column="code", property_name="internal_code", included=False),
        ]
        errors = validate_link_excluded_properties(links, properties)
        assert len(errors) == 1
        assert "excluded" in errors[0]["message"].lower()

    def test_missing_source_property_reported(self):
        from semantic.domain import EntityLink, PropertyMapping
        from semantic.validation import validate_link_excluded_properties

        links = [
            EntityLink(
                link_id="a",
                display_name="A",
                source_property_key="nonexistent",
                target_object_type_id="obj",
                target_property_key="id",
            ),
        ]
        properties = [
            PropertyMapping(source_column="id", property_name="ID", included=True),
        ]
        errors = validate_link_excluded_properties(links, properties)
        assert len(errors) == 1
        assert "not found" in errors[0]["message"].lower()

    def test_included_source_passes(self):
        from semantic.domain import EntityLink, PropertyMapping
        from semantic.validation import validate_link_excluded_properties

        links = [
            EntityLink(
                link_id="a",
                display_name="A",
                source_property_key="dept_id",
                target_object_type_id="obj",
                target_property_key="id",
            ),
        ]
        properties = [
            PropertyMapping(source_column="dept_id", property_name="dept_id", included=True),
        ]
        errors = validate_link_excluded_properties(links, properties)
        assert errors == []


class TestValidateLinkCardinality:
    def test_valid_cardinality_passes(self):
        from semantic.domain import EntityLink
        from semantic.validation import validate_link_cardinality

        links = [
            EntityLink(
                link_id="a",
                display_name="A",
                source_property_key="col",
                target_object_type_id="obj",
                target_property_key="id",
                cardinality="many_to_one",
            ),
            EntityLink(
                link_id="b",
                display_name="B",
                source_property_key="col2",
                target_object_type_id="obj2",
                target_property_key="id",
                cardinality="many_to_many",
            ),
        ]
        errors = validate_link_cardinality(links)
        assert errors == []

    def test_invalid_cardinality_blocked(self):
        from semantic.domain import EntityLink
        from semantic.validation import validate_link_cardinality

        links = [
            EntityLink(
                link_id="a",
                display_name="A",
                source_property_key="col",
                target_object_type_id="obj",
                target_property_key="id",
                cardinality="one_to_one",
            ),
        ]
        errors = validate_link_cardinality(links)
        assert len(errors) == 1
        assert "invalid cardinality" in errors[0]["message"].lower()


class TestValidateLinks:
    def test_valid_links_pass(self):
        from semantic.domain import EntityLink, PropertyMapping
        from semantic.validation import validate_links

        links = [
            EntityLink(
                link_id="dept_link",
                display_name="Department",
                source_property_key="dept_id",
                target_object_type_id="obj_dept",
                target_property_key="id",
            ),
        ]
        properties = [
            PropertyMapping(source_column="dept_id", property_name="dept_id", included=True),
        ]
        errors = validate_links(links, properties)
        assert errors == []

    def test_multiple_link_errors_reported(self):
        from semantic.domain import EntityLink, PropertyMapping
        from semantic.validation import validate_links

        links = [
            EntityLink(
                link_id="dup",
                display_name="A",
                source_property_key="excluded_col",
                target_object_type_id="obj",
                target_property_key="id",
            ),
            EntityLink(
                link_id="dup",
                display_name="B",
                source_property_key="excluded_col",
                target_object_type_id="obj",
                target_property_key="id",
            ),
        ]
        properties = [
            PropertyMapping(source_column="excluded", property_name="excluded_col", included=False),
        ]
        errors = validate_links(links, properties)
        # Should report: duplicate link_id, duplicate edge, excluded source property for each
        assert len(errors) >= 3

    def test_no_links_returns_empty(self):
        from semantic.validation import validate_links

        errors = validate_links([], [])
        assert errors == []


# ─── Computed Property Validation Tests ───


class TestValidateComputedPropertyIds:
    def test_unique_ids_pass(self):
        from semantic.domain import ComputedProperty
        from semantic.validation import validate_computed_property_ids

        cps = [
            ComputedProperty(id="cp_1", property_name="full_name"),
            ComputedProperty(id="cp_2", property_name="plant_status"),
        ]
        errors = validate_computed_property_ids(cps)
        assert errors == []

    def test_duplicate_ids_blocked(self):
        from semantic.domain import ComputedProperty
        from semantic.validation import validate_computed_property_ids

        cps = [
            ComputedProperty(id="cp_1", property_name="full_name"),
            ComputedProperty(id="cp_1", property_name="other"),
        ]
        errors = validate_computed_property_ids(cps)
        assert len(errors) == 1
        assert "duplicate" in errors[0]["message"].lower()

    def test_empty_id_blocked(self):
        from semantic.domain import ComputedProperty
        from semantic.validation import validate_computed_property_ids

        cps = [
            ComputedProperty(id="", property_name="full_name"),
        ]
        errors = validate_computed_property_ids(cps)
        assert len(errors) == 1
        assert "empty" in errors[0]["message"].lower()

    def test_no_computed_props_returns_empty(self):
        from semantic.validation import validate_computed_property_ids

        errors = validate_computed_property_ids([])
        assert errors == []


class TestValidateComputedPropertyNames:
    def test_unique_names_pass(self):
        from semantic.domain import ComputedProperty
        from semantic.validation import validate_computed_property_names

        cps = [
            ComputedProperty(id="cp_1", property_name="full_name", included=True),
            ComputedProperty(id="cp_2", property_name="plant_status", included=True),
        ]
        errors = validate_computed_property_names(cps, [])
        assert errors == []

    def test_duplicate_cp_names_blocked(self):
        from semantic.domain import ComputedProperty
        from semantic.validation import validate_computed_property_names

        cps = [
            ComputedProperty(id="cp_1", property_name="full_name", included=True),
            ComputedProperty(id="cp_2", property_name="Full_Name", included=True),
        ]
        errors = validate_computed_property_names(cps, [])
        assert len(errors) == 1
        assert "duplicate" in errors[0]["message"].lower()

    def test_conflict_with_ordinary_property_blocked(self):
        from semantic.domain import ComputedProperty, PropertyMapping
        from semantic.validation import validate_computed_property_names

        props = [
            PropertyMapping(source_column="col", property_name="full_name", included=True),
        ]
        cps = [
            ComputedProperty(id="cp_1", property_name="full_name", included=True),
        ]
        errors = validate_computed_property_names(cps, props)
        assert len(errors) == 1
        assert "conflicts" in errors[0]["message"].lower()

    def test_empty_name_blocked(self):
        from semantic.domain import ComputedProperty
        from semantic.validation import validate_computed_property_names

        cps = [
            ComputedProperty(id="cp_1", property_name="  ", included=True),
        ]
        errors = validate_computed_property_names(cps, [])
        assert len(errors) == 1
        assert "empty" in errors[0]["message"].lower()

    def test_excluded_cp_skipped(self):
        from semantic.domain import ComputedProperty
        from semantic.validation import validate_computed_property_names

        cps = [
            ComputedProperty(id="cp_1", property_name="", included=False),
        ]
        errors = validate_computed_property_names(cps, [])
        assert errors == []


class TestValidateComputedPropertyInputs:
    def test_valid_inputs_pass(self):
        from semantic.domain import ComputedProperty, FieldRef, SourceNode
        from semantic.validation import validate_computed_property_inputs

        sn = SourceNode(
            source_id="sn_1",
            source_type="dataset_table",
            name="employees",
            reference_id="ref_1",
            fields=["first_name", "last_name"],
        )
        cps = [
            ComputedProperty(
                id="cp_1",
                property_name="full_name",
                inputs=[
                    FieldRef(source_id="sn_1", source_name="employees", field_name="first_name"),
                    FieldRef(source_id="sn_1", source_name="employees", field_name="last_name"),
                ],
            ),
        ]
        errors = validate_computed_property_inputs(cps, [sn])
        assert errors == []

    def test_missing_inputs_blocked(self):
        from semantic.domain import ComputedProperty
        from semantic.validation import validate_computed_property_inputs

        cps = [
            ComputedProperty(id="cp_1", property_name="full_name", inputs=[]),
        ]
        errors = validate_computed_property_inputs(cps, [])
        assert len(errors) == 1
        assert "no input fields" in errors[0]["message"].lower()

    def test_missing_source_node_blocked(self):
        from semantic.domain import ComputedProperty, FieldRef, SourceNode
        from semantic.validation import validate_computed_property_inputs

        sn = SourceNode(
            source_id="sn_1",
            source_type="dataset_table",
            name="employees",
            reference_id="ref_1",
            fields=["first_name"],
        )
        cps = [
            ComputedProperty(
                id="cp_1",
                property_name="full_name",
                inputs=[
                    FieldRef(source_id="sn_missing", source_name="missing", field_name="col"),
                ],
            ),
        ]
        errors = validate_computed_property_inputs(cps, [sn])
        assert len(errors) == 1
        assert "not registered" in errors[0]["message"].lower()

    def test_missing_field_blocked(self):
        from semantic.domain import ComputedProperty, FieldRef, SourceNode
        from semantic.validation import validate_computed_property_inputs

        sn = SourceNode(
            source_id="sn_1",
            source_type="dataset_table",
            name="employees",
            reference_id="ref_1",
            fields=["first_name"],
        )
        cps = [
            ComputedProperty(
                id="cp_1",
                property_name="full_name",
                inputs=[
                    FieldRef(source_id="sn_1", source_name="employees", field_name="missing_col"),
                ],
            ),
        ]
        errors = validate_computed_property_inputs(cps, [sn])
        assert len(errors) == 1
        assert "not found" in errors[0]["message"].lower()


class TestValidateComputedPropertyAmbiguousRefs:
    def test_unambiguous_refs_pass(self):
        from semantic.domain import ComputedProperty, FieldRef, SourceNode
        from semantic.validation import validate_computed_property_ambiguous_refs

        sn1 = SourceNode(source_id="sn_1", source_type="dt", name="s1", reference_id="r1", fields=["col_a"])
        sn2 = SourceNode(source_id="sn_2", source_type="dt", name="s2", reference_id="r2", fields=["col_b"])
        cps = [
            ComputedProperty(
                id="cp_1",
                property_name="p",
                inputs=[
                    FieldRef(source_id="sn_1", source_name="s1", field_name="col_a"),
                    FieldRef(source_id="sn_2", source_name="s2", field_name="col_b"),
                ],
            ),
        ]
        errors = validate_computed_property_ambiguous_refs(cps, [sn1, sn2])
        assert errors == []

    def test_ambiguous_ref_blocked(self):
        from semantic.domain import ComputedProperty, FieldRef, SourceNode
        from semantic.validation import validate_computed_property_ambiguous_refs

        sn1 = SourceNode(source_id="sn_1", source_type="dt", name="s1", reference_id="r1", fields=["shared_col"])
        sn2 = SourceNode(source_id="sn_2", source_type="dt", name="s2", reference_id="r2", fields=["shared_col"])
        cps = [
            ComputedProperty(
                id="cp_1",
                property_name="p",
                inputs=[
                    FieldRef(source_id="", source_name="", field_name="shared_col"),
                ],
            ),
        ]
        errors = validate_computed_property_ambiguous_refs(cps, [sn1, sn2])
        assert len(errors) == 1
        assert "ambiguous" in errors[0]["message"].lower()

    def test_ambiguous_with_source_id_passes(self):
        from semantic.domain import ComputedProperty, FieldRef, SourceNode
        from semantic.validation import validate_computed_property_ambiguous_refs

        sn1 = SourceNode(source_id="sn_1", source_type="dt", name="s1", reference_id="r1", fields=["shared_col"])
        sn2 = SourceNode(source_id="sn_2", source_type="dt", name="s2", reference_id="r2", fields=["shared_col"])
        cps = [
            ComputedProperty(
                id="cp_1",
                property_name="p",
                inputs=[
                    FieldRef(source_id="sn_1", source_name="s1", field_name="shared_col"),
                ],
            ),
        ]
        errors = validate_computed_property_ambiguous_refs(cps, [sn1, sn2])
        assert errors == []


class TestValidateComputedPropertySemanticTypes:
    def test_valid_types_pass(self):
        from semantic.domain import ComputedProperty
        from semantic.validation import validate_computed_property_semantic_types

        cps = [
            ComputedProperty(id="cp_1", property_name="p", semantic_type="string"),
            ComputedProperty(id="cp_2", property_name="q", semantic_type="integer"),
        ]
        errors = validate_computed_property_semantic_types(cps)
        assert errors == []

    def test_invalid_type_blocked(self):
        from semantic.domain import ComputedProperty
        from semantic.validation import validate_computed_property_semantic_types

        cps = [
            ComputedProperty(id="cp_1", property_name="p", semantic_type="blob"),
        ]
        errors = validate_computed_property_semantic_types(cps)
        assert len(errors) == 1
        assert "invalid semantic type" in errors[0]["message"].lower()


class TestValidateComputedProperties:
    def test_valid_computed_props_pass(self):
        from semantic.domain import ComputedProperty, FieldRef, PropertyMapping, SourceNode
        from semantic.validation import validate_computed_properties

        sn = SourceNode(
            source_id="sn_1", source_type="dt", name="emp", reference_id="r1", fields=["first_name", "last_name"]
        )
        props = [PropertyMapping(source_column="id", property_name="ID", included=True)]
        cps = [
            ComputedProperty(
                id="cp_1",
                property_name="full_name",
                composition_kind="concat",
                expression="{first} {last}",
                included=True,
                inputs=[
                    FieldRef(source_id="sn_1", source_name="emp", field_name="first_name"),
                    FieldRef(source_id="sn_1", source_name="emp", field_name="last_name"),
                ],
            ),
        ]
        errors = validate_computed_properties(cps, props, [sn])
        assert errors == []

    def test_multiple_errors_reported(self):
        from semantic.domain import ComputedProperty, PropertyMapping
        from semantic.validation import validate_computed_properties

        props = [PropertyMapping(source_column="id", property_name="full_name", included=True)]
        cps = [
            ComputedProperty(id="", property_name="full_name", included=True, inputs=[]),
        ]
        errors = validate_computed_properties(cps, props, [])
        # Should report: empty id, conflicting name, no inputs
        assert len(errors) >= 3

    def test_no_computed_props_returns_empty(self):
        from semantic.validation import validate_computed_properties

        errors = validate_computed_properties([], [], [])
        assert errors == []
