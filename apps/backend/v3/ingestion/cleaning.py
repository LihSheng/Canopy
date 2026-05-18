from __future__ import annotations

from v3.ingestion.domain import CleaningStep, CleaningStepType, PipelineStatus

_STEP_TYPE_PARAMS: dict[str, dict[str, type]] = {
    "trim": {"columns": list},
    "rename": {"mappings": dict},
    "cast": {"columns": dict},
    "parse_date": {"columns": list},
    "dedupe": {"columns": list},
    "normalize_nulls": {"columns": list},
    "filter_empty_rows": {"threshold": float},
}

_VALID_STEP_TYPES = list(_STEP_TYPE_PARAMS)


def validate_step_type(step_type: str) -> list[str]:
    if step_type in _VALID_STEP_TYPES:
        return []
    return [f"Unknown step type: {step_type}"]


def validate_step_parameters(step_type: str, parameters: dict) -> list[str]:
    errors: list[str] = []
    if step_type not in _STEP_TYPE_PARAMS:
        return [f"Unknown step type: {step_type}"]

    expected = _STEP_TYPE_PARAMS[step_type]
    for key, expected_type in expected.items():
        if step_type == "filter_empty_rows" and key == "threshold" and key not in parameters:
            errors.append("Missing required parameter: threshold")
            continue
        if step_type == "filter_empty_rows" and key == "threshold":
            value = parameters.get(key, 0.5)
            if not isinstance(value, (int, float)):
                errors.append("threshold must be a number")
                continue
            if not 0 <= float(value) <= 1:
                errors.append("threshold must be between 0 and 1")
            continue

        if key not in parameters:
            errors.append(f"Missing required parameter: {key}")
            continue

        value = parameters[key]
        if expected_type is list and not isinstance(value, list):
            errors.append(f"{key} must be a list")
        elif expected_type is dict and not isinstance(value, dict):
            errors.append(f"{key} must be an object")

    if step_type == "dedupe" and parameters.get("keep", "first") not in {"first", "last"}:
        errors.append("keep must be one of: first, last")

    return errors


def validate_step_order(steps: list[CleaningStep]) -> list[str]:
    warnings: list[str] = []
    ordered = sorted(steps, key=lambda step: step.order)
    types = [step.step_type for step in ordered]
    if "rename" in types and "trim" in types and types.index("rename") < types.index("trim"):
        warnings.append("rename should run after trim")
    return warnings


def validate_pipeline(steps: list[CleaningStep], status: str) -> list[str]:
    warnings: list[str] = []
    if status == PipelineStatus.published.value and not steps:
        warnings.append("Published pipeline has no steps")
    for step in steps:
        warnings.extend(validate_step_type(step.step_type))
        warnings.extend(validate_step_parameters(step.step_type, step.parameters))
    warnings.extend(validate_step_order(steps))
    return warnings
