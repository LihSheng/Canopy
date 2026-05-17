import copy
import csv
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from common.config import settings
from v3.ingestion.domain import CleaningResult, CleaningStep, CleaningStepType

_DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d",
    "%Y-%m-%d %H:%M:%S", "%d-%b-%Y", "%b %d %Y",
]


def _get_cleaned_dir() -> Path:
    base = Path(settings.export_storage_dir or Path.home() / ".herd-aggregator")
    cleaned_dir = base / "cleaned"
    cleaned_dir.mkdir(parents=True, exist_ok=True)
    return cleaned_dir


def load_raw_rows(storage_path: str) -> list[dict]:
    path = Path(storage_path)
    ext = path.suffix.lower()
    if ext == ".csv":
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            return [dict(row) for row in reader]
    elif ext in (".xlsx", ".xls", ".xlsm"):
        from v3.ingestion.sources.xlsx import read_workbook
        sheets = read_workbook(path)
        if not sheets:
            return []
        sheet = sheets[0]
        rows_raw = sheet["rows"]
        if not rows_raw:
            return []
        header = [str(h) if h is not None else f"col_{i}" for i, h in enumerate(rows_raw[0])]
        result = []
        for row in rows_raw[1:]:
            d = {}
            for i, val in enumerate(row):
                if i < len(header):
                    d[header[i]] = val
            result.append(d)
        return result
    return []


def _apply_trim(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    columns = params.get("columns", [])
    warnings: list[str] = []
    result = []
    for row in rows:
        new_row = dict(row)
        for col in columns:
            if col in new_row and isinstance(new_row[col], str):
                new_row[col] = new_row[col].strip()
        result.append(new_row)
    return result, warnings


def _apply_rename(rows: list[dict], params: dict) -> tuple[list[dict], list[str], dict[str, str]]:
    mappings = params.get("mappings", {})
    warnings: list[str] = []
    rename_map: dict[str, str] = {}
    result = []
    for row in rows:
        new_row = {}
        for key, value in row.items():
            new_key = mappings.get(key, key)
            if new_key != key:
                rename_map[new_key] = key
            new_row[new_key] = value
        result.append(new_row)
    return result, warnings, rename_map


def _apply_cast(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    columns = params.get("columns", {})
    warnings: list[str] = []
    result = []
    for row in rows:
        new_row = dict(row)
        for col, target_type in columns.items():
            if col in new_row and new_row[col] is not None:
                val = new_row[col]
                try:
                    if target_type == "number":
                        if isinstance(val, str):
                            val = val.replace(",", "")
                        new_row[col] = float(val)
                    elif target_type == "text":
                        new_row[col] = str(val)
                    elif target_type == "date":
                        if isinstance(val, str):
                            parsed = False
                            for fmt in _DATE_FORMATS:
                                try:
                                    new_row[col] = datetime.strptime(val, fmt)
                                    parsed = True
                                    break
                                except ValueError:
                                    pass
                            if not parsed:
                                warnings.append(f"Could not cast column '{col}' to date")
                except (ValueError, TypeError):
                    warnings.append(f"Could not cast column '{col}' to {target_type}")
        result.append(new_row)
    return result, warnings


def _apply_parse_date(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    columns = params.get("columns", [])
    date_format: str | None = params.get("format")
    warnings: list[str] = []
    result = []
    for row in rows:
        new_row = dict(row)
        for col in columns:
            if col in new_row and isinstance(new_row[col], str) and new_row[col].strip():
                val = new_row[col].strip()
                try:
                    if date_format:
                        new_row[col] = datetime.strptime(val, date_format)
                    else:
                        parsed = False
                        for fmt in _DATE_FORMATS:
                            try:
                                new_row[col] = datetime.strptime(val, fmt)
                                parsed = True
                                break
                            except ValueError:
                                pass
                        if not parsed:
                            warnings.append(f"Could not parse date in column '{col}'")
                except ValueError:
                    warnings.append(f"Could not parse date in column '{col}'")
        result.append(new_row)
    return result, warnings


def _apply_dedupe(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    columns = params.get("columns", [])
    keep = params.get("keep", "first")
    warnings: list[str] = []
    seen: set[tuple] = set()
    result: list[dict] = []
    if keep == "last":
        for row in reversed(rows):
            key = tuple(row.get(col) for col in columns)
            if key not in seen:
                seen.add(key)
                result.append(row)
        result.reverse()
    else:
        for row in rows:
            key = tuple(row.get(col) for col in columns)
            if key not in seen:
                seen.add(key)
                result.append(row)
    return result, warnings


def _apply_normalize_nulls(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    columns = params.get("columns", [])
    replace_with = params.get("replace_with", "")
    warnings: list[str] = []
    result = []
    for row in rows:
        new_row = dict(row)
        for col in columns:
            if col in new_row and new_row[col] is None:
                new_row[col] = replace_with
        result.append(new_row)
    return result, warnings


def _apply_filter_empty_rows(rows: list[dict], params: dict) -> tuple[list[dict], list[str]]:
    threshold = params.get("threshold", 0.5)
    warnings: list[str] = []
    result = []
    for row in rows:
        if not row:
            continue
        values = list(row.values())
        null_count = sum(1 for v in values if v is None)
        null_ratio = null_count / len(values) if values else 1.0
        if null_ratio <= threshold:
            result.append(row)
    return result, warnings


def execute_cleaning_pipeline(raw_rows: list[dict], steps: list[CleaningStep]) -> CleaningResult:
    rows = copy.deepcopy(raw_rows)
    all_warnings: list[str] = []
    cumulative_rename_map: dict[str, str] = {}

    steps_sorted = sorted(steps, key=lambda s: s.order)

    for step in steps_sorted:
        step_type = step.step_type
        params = step.parameters

        try:
            if step_type == CleaningStepType.trim.value:
                rows, step_warnings = _apply_trim(rows, params)
                all_warnings.extend(step_warnings)
            elif step_type == CleaningStepType.rename.value:
                rows, step_warnings, rename_map = _apply_rename(rows, params)
                cumulative_rename_map.update(rename_map)
                all_warnings.extend(step_warnings)
            elif step_type == CleaningStepType.cast.value:
                rows, step_warnings = _apply_cast(rows, params)
                all_warnings.extend(step_warnings)
            elif step_type == CleaningStepType.parse_date.value:
                rows, step_warnings = _apply_parse_date(rows, params)
                all_warnings.extend(step_warnings)
            elif step_type == CleaningStepType.dedupe.value:
                rows, step_warnings = _apply_dedupe(rows, params)
                all_warnings.extend(step_warnings)
            elif step_type == CleaningStepType.normalize_nulls.value:
                rows, step_warnings = _apply_normalize_nulls(rows, params)
                all_warnings.extend(step_warnings)
            elif step_type == CleaningStepType.filter_empty_rows.value:
                rows, step_warnings = _apply_filter_empty_rows(rows, params)
                all_warnings.extend(step_warnings)
            else:
                all_warnings.append(f"Unknown step type '{step_type}', skipping")
        except Exception as e:
            all_warnings.append(f"Step '{step_type}' (order {step.order}) failed: {e}")
            return CleaningResult(
                rows=[],
                warnings=all_warnings,
                row_count=0,
                status="failed",
                rename_map=cumulative_rename_map,
            )

    if all_warnings:
        status = "completed_with_warnings"
    else:
        status = "completed"

    return CleaningResult(
        rows=rows,
        warnings=all_warnings,
        row_count=len(rows),
        status=status,
        rename_map=cumulative_rename_map,
    )


def parse_spec_steps(spec_json: dict) -> list[CleaningStep]:
    steps_data: Any = spec_json.get("steps", [])
    if not isinstance(steps_data, list):
        return []
    return [
        CleaningStep(
            id=str(uuid.uuid4()),
            step_type=s["step_type"],
            order=s.get("order", i),
            parameters=s.get("parameters", {}),
            description=s.get("description"),
        )
        for i, s in enumerate(steps_data)
    ]


def save_cleaned_rows(rows: list[dict], upload_id: str) -> str:
    cleaned_dir = _get_cleaned_dir()
    file_path = cleaned_dir / f"{upload_id}_cleaned.json"
    serializable = _make_serializable(rows)
    file_path.write_text(json.dumps(serializable, default=str, indent=2))
    return str(file_path)


def _make_serializable(rows: list[dict]) -> list[dict]:
    result = []
    for row in rows:
        new_row = {}
        for key, value in row.items():
            if isinstance(value, datetime):
                new_row[key] = value.isoformat()
            else:
                new_row[key] = value
        result.append(new_row)
    return result
