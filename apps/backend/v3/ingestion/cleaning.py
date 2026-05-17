from v3.ingestion.domain import CleaningStep, CleaningStepType, PipelineStatus


_STEP_TYPE_PARAMS: dict[str, dict] = {
    "trim": {"columns": {"type": "list", "required": True}},
    "rename": {"mappings": {"type": "dict", "required": True}},
    "cast": {"columns": {"type": "dict", "required": True}},
    "parse_date": {"columns": {"type": "list", "required": True}, "format": {"type": "str", "required": False}},
    "dedupe": {"columns": {"type": "list", "required": True}, "keep": {"type": "str", "required": False}},
    "normalize_nulls": {"columns": {"type": "list", "required": True}, "replace_with": {"type": "str", "required": False}},
    "filter_empty_rows": {"threshold": {"type": "float", "required": True}},
}

_VALID_STEP_TYPES = {e.value for e in CleaningStepType}


def validate_step_type(step_type: str) -> list[str]:
    if step_type not in _VALID_STEP_TYPES:
        return [f"Unknown step type '{step_type}'. Valid: {', '.join(sorted(_VALID_STEP_TYPES))}"]
    return []


def validate_step_parameters(step_type: str, parameters: dict) -> list[str]:
    errors: list[str] = []
    if step_type not in _VALID_STEP_TYPES:
        errors.append(f"Unknown step type '{step_type}'")
        return errors

    spec = _STEP_TYPE_PARAMS[step_type]
    for param_name, param_spec in spec.items():
        if param_spec["required"]:
            if param_name not in parameters or parameters[param_name] is None:
                errors.append(f"Missing required parameter '{param_name}' for step type '{step_type}'")
                continue

        value = parameters.get(param_name)
        if value is not None:
            expected = param_spec["type"]
            if expected == "list" and not isinstance(value, list):
                errors.append(f"Parameter '{param_name}' must be a list for step type '{step_type}'")
            elif expected == "dict" and not isinstance(value, dict):
                errors.append(f"Parameter '{param_name}' must be an object for step type '{step_type}'")
            elif expected == "str" and not isinstance(value, str):
                errors.append(f"Parameter '{param_name}' must be a string for step type '{step_type}'")
            elif expected == "float":
                if not isinstance(value, (int, float)):
                    errors.append(f"Parameter '{param_name}' must be a number for step type '{step_type}'")
                elif step_type == "filter_empty_rows" and not (0 < value <= 1):
                    errors.append(f"Parameter '{param_name}' must be between 0 and 1 for step type '{step_type}'")

    validate_keep = parameters.get("keep")
    if step_type == "dedupe" and validate_keep is not None and validate_keep not in ("first", "last"):
        errors.append(f"Parameter 'keep' must be 'first' or 'last' for step type 'dedupe', got '{validate_keep}'")

    return errors


def validate_step_order(steps: list[CleaningStep]) -> list[str]:
    warnings: list[str] = []
    seen_types: list[str] = []
    for step in steps:
        seen_types.append(step.step_type)

    rename_positions = [i for i, t in enumerate(seen_types) if t == "rename"]
    trim_positions = [i for i, t in enumerate(seen_types) if t == "trim"]

    for ri in rename_positions:
        for ti in trim_positions:
            if ti > ri:
                warnings.append(f"Step {ri + 1} (rename) is before step {ti + 1} (trim) — trim after rename may affect new names")
                break

    return warnings


def validate_pipeline(steps: list[CleaningStep], status: str) -> list[str]:
    all_warnings: list[str] = []
    for i, step in enumerate(steps):
        type_errors = validate_step_type(step.step_type)
        param_errors = validate_step_parameters(step.step_type, step.parameters)
        for e in type_errors + param_errors:
            all_warnings.append(f"Step {i + 1} ({step.step_type}): {e}")

    all_warnings.extend(validate_step_order(steps))

    if status == PipelineStatus.published.value and not steps:
        all_warnings.append("Cannot publish a pipeline with no steps")

    return all_warnings
