from datetime import datetime
from decimal import Decimal

from v3.ingestion.domain import MappingDecision, NormalizedOutput


def normalize_cleaned_rows(
    cleaned_rows: list[dict],
    mapping_decisions: list[MappingDecision],
    rename_map: dict[str, str] | None = None,
) -> NormalizedOutput:
    if rename_map is None:
        rename_map = {}

    original_to_ontology: dict[str, str] = {}
    for md in mapping_decisions:
        if md.confirmed:
            original_to_ontology[md.source_column_name] = md.target_field_name

    field_map: dict[str, str] = {}
    if cleaned_rows:
        for cleaned_col in cleaned_rows[0]:
            original_name = rename_map.get(cleaned_col, cleaned_col)
            if original_name in original_to_ontology:
                field_map[cleaned_col] = original_to_ontology[original_name]

    warnings: list[str] = []
    if cleaned_rows:
        all_cols = set(cleaned_rows[0].keys())
        mapped_cols = set(field_map.keys())
        unmapped = all_cols - mapped_cols
        if unmapped:
            warnings.append(f"Unmapped columns: {', '.join(sorted(unmapped))}")

    normalized_rows: list[dict] = []
    for row in cleaned_rows:
        new_row: dict = {}
        source_ref: dict[str, str] = {}
        for source_col, value in row.items():
            target = field_map.get(source_col, source_col)
            if source_col in field_map:
                source_ref[target] = rename_map.get(source_col, source_col)

            if isinstance(value, datetime):
                new_row[target] = value.isoformat()
            elif isinstance(value, float):
                new_row[target] = str(Decimal(str(value)))
            else:
                new_row[target] = value

        new_row["_source_ref"] = source_ref
        normalized_rows.append(new_row)

    return NormalizedOutput(
        rows=normalized_rows,
        field_map=field_map,
        warnings=warnings,
    )
