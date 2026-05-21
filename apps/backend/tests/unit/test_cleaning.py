import uuid

from ingestion.cleaning import (
    validate_pipeline,
    validate_step_order,
    validate_step_parameters,
    validate_step_type,
)
from ingestion.domain import CleaningPipeline, CleaningStep, PipelineStatus


def _step(
    step_type: str,
    order: int = 0,
    parameters: dict | None = None,
    description: str | None = None,
) -> CleaningStep:
    return CleaningStep(
        id=str(uuid.uuid4()),
        step_type=step_type,
        order=order,
        parameters=parameters or {},
        description=description,
    )


class TestValidateStepType:
    def test_accepts_valid_step_types(self):
        for t in ("trim", "rename", "cast", "parse_date", "dedupe", "normalize_nulls", "filter_empty_rows"):
            assert validate_step_type(t) == []

    def test_rejects_unknown_type(self):
        errors = validate_step_type("unknown_type")
        assert len(errors) == 1
        assert "Unknown" in errors[0]


class TestValidateStepParameters:
    def test_trim_requires_columns(self):
        errors = validate_step_parameters("trim", {})
        assert any("columns" in e for e in errors)

    def test_trim_accepts_valid_columns(self):
        errors = validate_step_parameters("trim", {"columns": ["name", "email"]})
        assert errors == []

    def test_trim_rejects_non_list_columns(self):
        errors = validate_step_parameters("trim", {"columns": "name"})
        assert any("must be a list" in e for e in errors)

    def test_rename_requires_mappings(self):
        errors = validate_step_parameters("rename", {})
        assert any("mappings" in e for e in errors)

    def test_rename_accepts_valid_mappings(self):
        errors = validate_step_parameters("rename", {"mappings": {"old": "new"}})
        assert errors == []

    def test_rename_rejects_non_dict_mappings(self):
        errors = validate_step_parameters("rename", {"mappings": ["old"]})
        assert any("must be an object" in e for e in errors)

    def test_cast_requires_columns(self):
        errors = validate_step_parameters("cast", {})
        assert any("columns" in e for e in errors)

    def test_cast_accepts_valid_columns(self):
        errors = validate_step_parameters("cast", {"columns": {"age": "number"}})
        assert errors == []

    def test_parse_date_requires_columns(self):
        errors = validate_step_parameters("parse_date", {})
        assert any("columns" in e for e in errors)

    def test_parse_date_accepts_valid_params(self):
        errors = validate_step_parameters("parse_date", {"columns": ["date_col"], "format": "%Y-%m-%d"})
        assert errors == []

    def test_dedupe_requires_columns(self):
        errors = validate_step_parameters("dedupe", {})
        assert any("columns" in e for e in errors)

    def test_dedupe_accepts_valid_keep(self):
        errors = validate_step_parameters("dedupe", {"columns": ["id"], "keep": "first"})
        assert errors == []

    def test_dedupe_rejects_invalid_keep(self):
        errors = validate_step_parameters("dedupe", {"columns": ["id"], "keep": "all"})
        assert any("keep" in e for e in errors)

    def test_normalize_nulls_requires_columns(self):
        errors = validate_step_parameters("normalize_nulls", {})
        assert any("columns" in e for e in errors)

    def test_normalize_nulls_accepts_valid(self):
        errors = validate_step_parameters("normalize_nulls", {"columns": ["col1"], "replace_with": "N/A"})
        assert errors == []

    def test_filter_empty_rows_requires_threshold(self):
        errors = validate_step_parameters("filter_empty_rows", {})
        assert any("threshold" in e for e in errors)

    def test_filter_empty_rows_accepts_valid_threshold(self):
        errors = validate_step_parameters("filter_empty_rows", {"threshold": 0.5})
        assert errors == []

    def test_filter_empty_rows_rejects_out_of_range(self):
        errors = validate_step_parameters("filter_empty_rows", {"threshold": 1.5})
        assert any("between 0 and 1" in e for e in errors)


class TestValidateStepOrder:
    def test_no_warnings_for_trim_before_rename(self):
        steps = [
            _step("trim", 0),
            _step("rename", 1),
        ]
        warnings = validate_step_order(steps)
        assert warnings == []

    def test_warning_for_rename_before_trim(self):
        steps = [
            _step("rename", 0, {"mappings": {"old": "new"}}),
            _step("trim", 1, {"columns": ["new"]}),
        ]
        warnings = validate_step_order(steps)
        assert any("rename" in w and "trim" in w for w in warnings)

    def test_no_warnings_for_single_step(self):
        steps = [_step("trim", 0)]
        assert validate_step_order(steps) == []

    def test_no_warnings_for_unrelated_sequence(self):
        steps = [
            _step("trim", 0),
            _step("cast", 1),
            _step("dedupe", 2),
        ]
        assert validate_step_order(steps) == []


class TestValidatePipeline:
    def test_valid_pipeline_returns_no_errors(self):
        steps = [
            _step("trim", 0, {"columns": ["name"]}),
            _step("rename", 1, {"mappings": {"name": "full_name"}}),
        ]
        warnings = validate_pipeline(steps, "draft")
        assert all("error" not in w.lower() and "missing" not in w.lower() for w in warnings)

    def test_pipeline_with_invalid_steps_reports_errors(self):
        steps = [_step("unknown", 0)]
        warnings = validate_pipeline(steps, "draft")
        assert any("Unknown" in w for w in warnings)

    def test_pipeline_with_missing_params_reports_errors(self):
        steps = [_step("trim", 0)]
        warnings = validate_pipeline(steps, "draft")
        assert any("columns" in w for w in warnings)

    def test_publish_with_no_steps_reports_warning(self):
        warnings = validate_pipeline([], "published")
        assert any("no steps" in w for w in warnings)

    def test_pipeline_serialization_roundtrip(self):
        steps = [
            _step("trim", 0, {"columns": ["name"]}),
            _step("dedupe", 1, {"columns": ["id"], "keep": "first"}),
        ]
        pipeline = CleaningPipeline(
            id=str(uuid.uuid4()),
            upload_id=str(uuid.uuid4()),
            steps=steps,
            status=PipelineStatus.draft.value,
        )
        assert pipeline.status == "draft"
        assert len(pipeline.steps) == 2
        assert pipeline.steps[0].step_type == "trim"
        assert pipeline.steps[1].step_type == "dedupe"

    def test_draft_to_published_transition_allowed_when_valid(self):
        steps = [
            _step("trim", 0, {"columns": ["name"]}),
        ]
        warnings = validate_pipeline(steps, PipelineStatus.published.value)
        error_warnings = [w for w in warnings if "error" in w.lower() or "missing" in w.lower()]
        assert len(error_warnings) == 0

    def test_draft_to_published_blocked_when_invalid(self):
        steps = [_step("trim", 0)]
        warnings = validate_pipeline(steps, PipelineStatus.published.value)
        assert any("columns" in w for w in warnings)
