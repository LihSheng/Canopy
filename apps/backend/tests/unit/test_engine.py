import uuid
from datetime import datetime

import pytest

from v3.ingestion.cleaning import validate_step_parameters, validate_step_type
from v3.ingestion.domain import CleaningResult, CleaningStep, MappingDecision
from v3.ingestion.engine import (
    _apply_cast,
    _apply_dedupe,
    _apply_filter_empty_rows,
    _apply_normalize_nulls,
    _apply_parse_date,
    _apply_rename,
    _apply_trim,
    execute_cleaning_pipeline,
    parse_spec_steps,
)
from v3.ingestion.normalization import normalize_cleaned_rows


def _step(step_type: str, order: int = 0, parameters: dict | None = None) -> CleaningStep:
    return CleaningStep(
        id=str(uuid.uuid4()),
        step_type=step_type,
        order=order,
        parameters=parameters or {},
    )


class TestApplyTrim:
    def test_trims_whitespace_from_specified_columns(self):
        rows = [{"name": "  Alice  ", "email": "  a@b.com  "}]
        result, warnings = _apply_trim(rows, {"columns": ["name"]})
        assert result[0]["name"] == "Alice"
        assert result[0]["email"] == "  a@b.com  "
        assert warnings == []

    def test_handles_non_string_values(self):
        rows = [{"name": "Alice", "age": 30}]
        result, warnings = _apply_trim(rows, {"columns": ["age"]})
        assert result[0]["age"] == 30

    def test_handles_empty_columns_list(self):
        rows = [{"name": "  Alice  "}]
        result, warnings = _apply_trim(rows, {"columns": []})
        assert result[0]["name"] == "  Alice  "

    def test_handles_missing_column(self):
        rows = [{"name": "Alice"}]
        result, warnings = _apply_trim(rows, {"columns": ["missing"]})
        assert result[0]["name"] == "Alice"


class TestApplyRename:
    def test_renames_columns_per_mappings(self):
        rows = [{"old_name": "Alice", "old_age": 30}]
        result, warnings, rename_map = _apply_rename(rows, {"mappings": {"old_name": "new_name"}})
        assert "new_name" in result[0]
        assert "old_name" not in result[0]
        assert result[0]["new_name"] == "Alice"
        assert result[0]["old_age"] == 30
        assert rename_map == {"new_name": "old_name"}

    def test_handles_empty_mappings(self):
        rows = [{"name": "Alice"}]
        result, warnings, rename_map = _apply_rename(rows, {"mappings": {}})
        assert result[0]["name"] == "Alice"
        assert rename_map == {}

    def test_handles_multiple_renames(self):
        rows = [{"a": 1, "b": 2}]
        result, warnings, rename_map = _apply_rename(rows, {"mappings": {"a": "x", "b": "y"}})
        assert "x" in result[0] and "y" in result[0]
        assert "a" not in result[0] and "b" not in result[0]
        assert len(rename_map) == 2


class TestApplyCast:
    def test_casts_to_number(self):
        rows = [{"amount": "100.5"}]
        result, warnings = _apply_cast(rows, {"columns": {"amount": "number"}})
        assert isinstance(result[0]["amount"], float)
        assert result[0]["amount"] == 100.5

    def test_casts_to_text(self):
        rows = [{"age": 30}]
        result, warnings = _apply_cast(rows, {"columns": {"age": "text"}})
        assert isinstance(result[0]["age"], str)
        assert result[0]["age"] == "30"

    def test_emits_warning_on_cast_failure(self):
        rows = [{"amount": "not_a_number"}]
        result, warnings = _apply_cast(rows, {"columns": {"amount": "number"}})
        assert any("Could not cast" in w for w in warnings)

    def test_handles_none_values(self):
        rows = [{"amount": None}]
        result, warnings = _apply_cast(rows, {"columns": {"amount": "number"}})
        assert result[0]["amount"] is None

    def test_handles_empty_columns(self):
        rows = [{"name": "Alice"}]
        result, warnings = _apply_cast(rows, {"columns": {}})
        assert result[0]["name"] == "Alice"

    def test_casts_number_with_commas(self):
        rows = [{"amount": "1,234.56"}]
        result, warnings = _apply_cast(rows, {"columns": {"amount": "number"}})
        assert result[0]["amount"] == 1234.56


class TestApplyParseDate:
    def test_parses_with_format(self):
        rows = [{"date": "2024-01-15"}]
        result, warnings = _apply_parse_date(rows, {"columns": ["date"], "format": "%Y-%m-%d"})
        assert isinstance(result[0]["date"], datetime)
        assert result[0]["date"].year == 2024
        assert result[0]["date"].month == 1
        assert result[0]["date"].day == 15

    def test_parses_without_format(self):
        rows = [{"date": "15/01/2024"}]
        result, warnings = _apply_parse_date(rows, {"columns": ["date"]})
        assert isinstance(result[0]["date"], datetime)

    def test_emits_warning_on_failure(self):
        rows = [{"date": "not-a-date"}]
        result, warnings = _apply_parse_date(rows, {"columns": ["date"]})
        assert any("Could not parse" in w for w in warnings)

    def test_handles_empty_string(self):
        rows = [{"date": ""}]
        result, warnings = _apply_parse_date(rows, {"columns": ["date"]})
        assert result[0]["date"] == ""
        assert warnings == []

    def test_handles_none_value(self):
        rows = [{"date": None}]
        result, warnings = _apply_parse_date(rows, {"columns": ["date"]})
        assert result[0]["date"] is None


class TestApplyDedupe:
    def test_removes_duplicates_keep_first(self):
        rows = [{"id": 1, "name": "Alice"}, {"id": 1, "name": "Bob"}, {"id": 2, "name": "Charlie"}]
        result, warnings = _apply_dedupe(rows, {"columns": ["id"], "keep": "first"})
        assert len(result) == 2
        assert result[0]["name"] == "Alice"

    def test_keeps_last_when_specified(self):
        rows = [{"id": 1, "name": "Alice"}, {"id": 1, "name": "Bob"}]
        result, warnings = _apply_dedupe(rows, {"columns": ["id"], "keep": "last"})
        assert len(result) == 1
        assert result[0]["name"] == "Bob"

    def test_defaults_to_keep_first(self):
        rows = [{"id": 1, "name": "Alice"}, {"id": 1, "name": "Bob"}]
        result, warnings = _apply_dedupe(rows, {"columns": ["id"]})
        assert len(result) == 1
        assert result[0]["name"] == "Alice"

    def test_no_duplicates(self):
        rows = [{"id": 1}, {"id": 2}]
        result, warnings = _apply_dedupe(rows, {"columns": ["id"]})
        assert len(result) == 2

    def test_dedupe_on_multiple_columns(self):
        rows = [{"a": 1, "b": 2}, {"a": 1, "b": 2}, {"a": 1, "b": 3}]
        result, warnings = _apply_dedupe(rows, {"columns": ["a", "b"]})
        assert len(result) == 2


class TestApplyNormalizeNulls:
    def test_replaces_none_with_specified_value(self):
        rows = [{"name": None, "email": "a@b.com"}]
        result, warnings = _apply_normalize_nulls(rows, {"columns": ["name"], "replace_with": "N/A"})
        assert result[0]["name"] == "N/A"

    def test_defaults_to_empty_string(self):
        rows = [{"name": None}]
        result, warnings = _apply_normalize_nulls(rows, {"columns": ["name"]})
        assert result[0]["name"] == ""

    def test_does_not_affect_non_null_values(self):
        rows = [{"name": "Alice"}]
        result, warnings = _apply_normalize_nulls(rows, {"columns": ["name"], "replace_with": "N/A"})
        assert result[0]["name"] == "Alice"

    def test_skips_missing_column(self):
        rows = [{"name": "Alice"}]
        result, warnings = _apply_normalize_nulls(rows, {"columns": ["missing"]})
        assert result[0]["name"] == "Alice"


class TestApplyFilterEmptyRows:
    def test_removes_rows_above_threshold(self):
        rows = [{"a": 1, "b": None, "c": None}, {"a": 1, "b": 2, "c": 3}]
        result, warnings = _apply_filter_empty_rows(rows, {"threshold": 0.5})
        assert len(result) == 1
        assert result[0]["a"] == 1

    def test_keeps_rows_at_threshold(self):
        rows = [{"a": 1, "b": None}]
        result, warnings = _apply_filter_empty_rows(rows, {"threshold": 0.5})
        assert len(result) == 1

    def test_defaults_threshold_to_0_5(self):
        rows = [{"a": None}]
        result, warnings = _apply_filter_empty_rows(rows, {})
        assert len(result) == 0

    def test_handles_empty_rows(self):
        rows: list[dict] = []
        result, warnings = _apply_filter_empty_rows(rows, {"threshold": 0.5})
        assert result == []


class TestExecuteCleaningPipeline:
    def test_steps_execute_in_order(self):
        rows = [{"  name  ": "  Alice  "}]
        steps = [
            _step("trim", 0, {"columns": ["  name  "]}),
            _step("rename", 1, {"mappings": {"  name  ": "name"}}),
        ]
        result = execute_cleaning_pipeline(rows, steps)
        assert result.rows[0]["name"] == "Alice"
        assert result.status == "completed"

    def test_empty_input_returns_empty(self):
        result = execute_cleaning_pipeline([], [])
        assert result.rows == []
        assert result.row_count == 0

    def test_unknown_step_type_generates_warning(self):
        rows = [{"name": "Alice"}]
        steps = [_step("unknown_type", 0)]
        result = execute_cleaning_pipeline(rows, steps)
        assert any("Unknown" in w for w in result.warnings)

    def test_dedupe_step_removes_duplicates_in_pipeline(self):
        rows = [{"id": 1, "v": "a"}, {"id": 1, "v": "b"}, {"id": 2, "v": "c"}]
        steps = [_step("dedupe", 0, {"columns": ["id"]})]
        result = execute_cleaning_pipeline(rows, steps)
        assert result.row_count == 2
        assert result.rows[0]["v"] == "a"

    def test_full_pipeline_with_all_steps(self):
        rows = [
            {"  name  ": "  Alice  ", "age": "30", "date": "2024-01-15", "city": None},
            {"  name  ": "  Bob  ", "age": "25", "date": "2024-02-20", "city": "NYC"},
        ]
        steps = [
            _step("trim", 0, {"columns": ["  name  "]}),
            _step("rename", 1, {"mappings": {"  name  ": "name"}}),
            _step("cast", 2, {"columns": {"age": "number"}}),
            _step("parse_date", 3, {"columns": ["date"], "format": "%Y-%m-%d"}),
        ]
        result = execute_cleaning_pipeline(rows, steps)
        assert result.row_count == 2
        assert isinstance(result.rows[0]["age"], float)
        assert isinstance(result.rows[0]["date"], datetime)
        assert result.rows[0]["name"] == "Alice"

    def test_status_completed_with_warnings(self):
        rows = [{"val": "x"}]
        steps = [_step("cast", 0, {"columns": {"val": "number"}})]
        result = execute_cleaning_pipeline(rows, steps)
        assert result.status == "completed_with_warnings"

    def test_immutable_input_preserved(self):
        original = [{"name": "  Alice  "}]
        rows_before = [dict(r) for r in original]
        steps = [_step("trim", 0, {"columns": ["name"]})]
        execute_cleaning_pipeline(original, steps)
        assert original == rows_before

    def test_rename_map_tracking(self):
        rows = [{"old_name": "Alice"}]
        steps = [_step("rename", 0, {"mappings": {"old_name": "new_name"}})]
        result = execute_cleaning_pipeline(rows, steps)
        assert result.rename_map == {"new_name": "old_name"}

    def test_rename_map_multiple_steps(self):
        rows = [{"a": 1}]
        steps = [
            _step("rename", 0, {"mappings": {"a": "b"}}),
            _step("rename", 1, {"mappings": {"b": "c"}}),
        ]
        result = execute_cleaning_pipeline(rows, steps)
        assert result.rename_map == {"b": "a", "c": "b"}

    def test_error_in_step_returns_failed_status(self):
        rows = [{"val": "x"}]
        steps = [_step("filter_empty_rows", 0, {"threshold": "invalid"})]
        result = execute_cleaning_pipeline(rows, steps)
        assert result.status == "failed"


class TestParseSpecSteps:
    def test_parses_steps_from_spec(self):
        spec = {
            "steps": [
                {"step_type": "trim", "order": 0, "parameters": {"columns": ["name"]}},
                {"step_type": "rename", "order": 1, "parameters": {"mappings": {"name": "full_name"}}},
            ]
        }
        steps = parse_spec_steps(spec)
        assert len(steps) == 2
        assert steps[0].step_type == "trim"
        assert steps[1].step_type == "rename"
        assert steps[0].parameters == {"columns": ["name"]}

    def test_handles_empty_spec(self):
        steps = parse_spec_steps({})
        assert steps == []

    def test_handles_missing_steps_key(self):
        steps = parse_spec_steps({"other": "data"})
        assert steps == []


class TestNormalization:
    def test_normalizes_rows_with_mapping_decisions(self):
        rows = [{"name": "Alice", "amount": 100.5}]
        decisions = [
            MappingDecision(source_column_name="name", target_field_name="employee_name", confirmed=True, overridden_by_user=False),
            MappingDecision(source_column_name="amount", target_field_name="salary", confirmed=True, overridden_by_user=False),
        ]
        output = normalize_cleaned_rows(rows, decisions)
        assert "employee_name" in output.rows[0]
        assert "salary" in output.rows[0]
        assert output.rows[0]["employee_name"] == "Alice"
        assert "_source_ref" in output.rows[0]

    def test_normalizes_number_as_decimal_string(self):
        rows = [{"amount": 100.5}]
        decisions = [
            MappingDecision(source_column_name="amount", target_field_name="salary", confirmed=True, overridden_by_user=False),
        ]
        output = normalize_cleaned_rows(rows, decisions)
        assert isinstance(output.rows[0]["salary"], str)
        assert output.rows[0]["salary"] == "100.5"

    def test_normalizes_date_as_iso_string(self):
        rows = [{"date": datetime(2024, 1, 15)}]
        decisions = [
            MappingDecision(source_column_name="date", target_field_name="submitted_at", confirmed=True, overridden_by_user=False),
        ]
        output = normalize_cleaned_rows(rows, decisions)
        assert output.rows[0]["submitted_at"] == "2024-01-15T00:00:00"

    def test_warns_on_unmapped_columns(self):
        rows = [{"name": "Alice", "extra_col": "x"}]
        decisions = [
            MappingDecision(source_column_name="name", target_field_name="employee_name", confirmed=True, overridden_by_user=False),
        ]
        output = normalize_cleaned_rows(rows, decisions)
        assert any("Unmapped" in w for w in output.warnings)

    def test_renamed_columns_resolve_mapping(self):
        rows = [{"new_name": "Alice"}]
        decisions = [
            MappingDecision(source_column_name="old_name", target_field_name="employee_name", confirmed=True, overridden_by_user=False),
        ]
        rename_map = {"new_name": "old_name"}
        output = normalize_cleaned_rows(rows, decisions, rename_map)
        assert "employee_name" in output.rows[0]
        assert output.rows[0]["employee_name"] == "Alice"

    def test_field_map_contains_correct_mapping(self):
        rows = [{"name": "Alice"}]
        decisions = [
            MappingDecision(source_column_name="name", target_field_name="employee_name", confirmed=True, overridden_by_user=False),
        ]
        output = normalize_cleaned_rows(rows, decisions)
        assert output.field_map == {"name": "employee_name"}

    def test_empty_rows_returns_empty(self):
        output = normalize_cleaned_rows([], [])
        assert output.rows == []
        assert output.field_map == {}
