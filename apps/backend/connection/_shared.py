from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path

from common.config import settings


def storage_root() -> Path:
    if settings.export_storage_dir:
        return Path(settings.export_storage_dir) / "data-sources"
    return Path(__file__).resolve().parents[2] / "storage" / "data-sources"


def is_empty_row(values: Iterable[object | None]) -> bool:
    for value in values:
        if value not in (None, ""):
            return False
    return True


def normalize_header(values: list[object | None], column_count: int) -> list[str]:
    headers: list[str] = []
    for index in range(column_count):
        value = values[index] if index < len(values) else None
        if value in (None, ""):
            headers.append(f"column_{index + 1}")
        else:
            headers.append(str(value))
    return headers


def normalize_preview_row(values: list[object | None], column_count: int) -> list[object | None]:
    row: list[object | None] = []
    for index in range(column_count):
        row.append(values[index] if index < len(values) else None)
    return row


def write_jsonl_version(rows: list[dict], dataset_id: str, sheet_name: str) -> Path:
    version_dir = storage_root() / dataset_id
    version_dir.mkdir(parents=True, exist_ok=True)
    version_path = version_dir / f"{slugify(sheet_name)}.jsonl"
    with open(version_path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, default=str))
            handle.write("\n")
    return version_path


def slugify(value: str) -> str:
    cleaned = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif cleaned and cleaned[-1] != "-":
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    return slug or "sheet"
