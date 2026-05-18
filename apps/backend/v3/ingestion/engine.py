from __future__ import annotations

import copy
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from common.config import settings
from v3.ingestion.cleaning import validate_step_parameters, validate_step_type
from v3.ingestion.domain import CleaningResult, CleaningStep, CleaningStepType

_DATE_FORMATS = ["%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%dT%H:%M:%S"]


def _get_cleaned_dir() -> Path:
    if settings.export_storage_dir:
        base = Path(settings.export_storage_dir)
    else:
        base = Path(__file__).resolve().parents[2] / "storage"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _apply_trim(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    columns = params.get("columns", [])
    output = copy.deepcopy(rows)
    for row in output:
        for column in columns:
            if isinstance(row.get(column), str):
                row[column] = row[column].strip()
    return output, []


def _apply_rename(rows: list[dict], params: dict) -> tuple[list[dict], list[str], dict[str, str]]:
    mappings = params.get("mappings", {})
    output = copy.deepcopy(rows)
    rename_map: dict[str, str] = {}
    for row in output:
        for old_name, new_name in mappings.items():
            if old_name in row:
                row[new_name] = row.pop(old_name)
                rename_map[new_name] = old_name
    return output, [], rename_map


def _apply_cast(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    columns = params.get("columns", {})
    output = copy.deepcopy(rows)
    warnings: list[str] = []
    for row in output:
        for column, target_type in columns.items():
            if column not in row or row[column] is None:
                continue
            try:
                if target_type == "number":
                    value = str(row[column]).replace(",", "")
                    row[column] = float(value)
                elif target_type == "text":
                    row[column] = str(row[column])
                else:
                    warnings.append(f"Unsupported cast type for {column}: {target_type}")
            except Exception:
                warnings.append(f"Could not cast {column} to {target_type}")
    return output, warnings


def _parse_date_value(value, format_hint: str | None = None):
    if value in (None, ""):
        return value
    if isinstance(value, datetime):
        return value
    text = str(value)
    if format_hint:
        return datetime.strptime(text, format_hint)
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(text)


def _apply_parse_date(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    columns = params.get("columns", [])
    format_hint = params.get("format")
    output = copy.deepcopy(rows)
    warnings: list[str] = []
    for row in output:
        for column in columns:
            try:
                row[column] = _parse_date_value(row.get(column), format_hint)
            except Exception:
                warnings.append(f"Could not parse {column}")
    return output, warnings


def _apply_dedupe(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    columns = params.get("columns", [])
    keep = params.get("keep", "first")
    if not columns:
        return copy.deepcopy(rows), []
    seen = {}
    ordered_keys: list[tuple] = []
    for row in rows:
        key = tuple(row.get(column) for column in columns)
        if key not in seen:
            ordered_keys.append(key)
        if keep == "last" or key not in seen:
            seen[key] = copy.deepcopy(row)
    if keep == "last":
        output = [seen[key] for key in ordered_keys]
    else:
        output = [seen[key] for key in ordered_keys]
    return output, []


def _apply_normalize_nulls(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    columns = params.get("columns", [])
    replace_with = params.get("replace_with", "")
    output = copy.deepcopy(rows)
    for row in output:
        for column in columns:
            if column in row and row[column] is None:
                row[column] = replace_with
    return output, []


def _apply_filter_empty_rows(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    threshold = params.get("threshold", 0.5)
    if not isinstance(threshold, (int, float)):
        raise ValueError("threshold must be numeric")
    output: list[dict] = []
    for row in rows:
        if not row:
            continue
        values = list(row.values())
        empty_count = sum(1 for value in values if value in (None, ""))
        ratio = empty_count / max(len(values), 1)
        if ratio <= float(threshold):
            output.append(copy.deepcopy(row))
    return output, []


def parse_spec_steps(spec: dict) -> list[CleaningStep]:
    steps = spec.get("steps", []) or []
    output = []
    for index, step in enumerate(steps):
        output.append(
            CleaningStep(
                id=str(step.get("id", index)),
                step_type=step.get("step_type") or step.get("type") or "",
                order=int(step.get("order", index)),
                parameters=step.get("parameters", {}) or {},
                description=step.get("description"),
            )
        )
    return output


def _make_serializable(value: Any):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_make_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: _make_serializable(item) for key, item in value.items()}
    return value


def save_cleaned_rows(rows: list[dict], upload_id: str) -> Path:
    cleaned_dir = _get_cleaned_dir() / upload_id
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    path = cleaned_dir / "cleaned.json"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump([_make_serializable(row) for row in rows], handle, ensure_ascii=False)
    return path


def execute_cleaning_pipeline(rows: list[dict], steps: list[CleaningStep]) -> CleaningResult:
    working = copy.deepcopy(rows)
    warnings: list[str] = []
    rename_map: dict[str, str] = {}
    try:
        for step in sorted(steps, key=lambda item: item.order):
            warnings.extend(validate_step_type(step.step_type))
            warnings.extend(validate_step_parameters(step.step_type, step.parameters))
            if step.step_type == CleaningStepType.trim.value:
                working, step_warnings = _apply_trim(working, step.parameters)
            elif step.step_type == CleaningStepType.rename.value:
                working, step_warnings, step_rename_map = _apply_rename(working, step.parameters)
                rename_map.update(step_rename_map)
            elif step.step_type == CleaningStepType.cast.value:
                working, step_warnings = _apply_cast(working, step.parameters)
            elif step.step_type == CleaningStepType.parse_date.value:
                working, step_warnings = _apply_parse_date(working, step.parameters)
            elif step.step_type == CleaningStepType.dedupe.value:
                working, step_warnings = _apply_dedupe(working, step.parameters)
            elif step.step_type == CleaningStepType.normalize_nulls.value:
                working, step_warnings = _apply_normalize_nulls(working, step.parameters)
            elif step.step_type == CleaningStepType.filter_empty_rows.value:
                working, step_warnings = _apply_filter_empty_rows(working, step.parameters)
            else:
                step_warnings = [f"Unknown step type: {step.step_type}"]
            warnings.extend(step_warnings)

        status = "completed_with_warnings" if warnings else "completed"
        return CleaningResult(
            rows=working,
            warnings=warnings,
            rename_map=rename_map,
            row_count=len(working),
            status=status,
        )
    except Exception as exc:
        return CleaningResult(
            rows=working,
            warnings=warnings + [str(exc)],
            rename_map=rename_map,
            row_count=len(working),
            status="failed",
        )

