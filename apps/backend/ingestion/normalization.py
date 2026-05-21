from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from ingestion.domain import MappingDecision, NormalizedOutput


def _normalize_value(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, float) or isinstance(value, int):
        return str(value)
    return value


def normalize_cleaned_rows(
    cleaned_rows: list[dict],
    mapping_decisions: list[MappingDecision],
    rename_map: dict[str, str] | None = None,
) -> NormalizedOutput:
    rename_map = rename_map or {}
    source_to_target = {decision.source_column_name: decision.target_field_name for decision in mapping_decisions}
    output_rows: list[dict] = []
    warnings: list[str] = []

    for index, row in enumerate(cleaned_rows):
        normalized: dict = {"_source_ref": {"row_index": index}}
        for source_column, target_field in source_to_target.items():
            actual_column = next((k for k, v in rename_map.items() if v == source_column), source_column)
            if actual_column in row:
                normalized[target_field] = _normalize_value(row[actual_column])

        unmapped = [key for key in row.keys() if key not in rename_map.values() and key not in source_to_target]
        if unmapped:
            warnings.append(f"Unmapped columns: {', '.join(sorted(unmapped))}")
        output_rows.append(normalized)

    return NormalizedOutput(rows=output_rows, field_map=source_to_target, warnings=warnings)
