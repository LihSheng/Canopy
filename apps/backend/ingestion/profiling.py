from __future__ import annotations

from datetime import datetime

from ingestion.domain import ColumnProfile, SheetProfile, UploadStatus, WorkbookProfile


def _infer_value_type(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return "number"
    if isinstance(value, datetime):
        return "date"
    if isinstance(value, str):
        try:
            datetime.fromisoformat(value)
            return "date"
        except ValueError:
            return "text"
    return "text"


def _infer_type_from_values(values: list) -> str:
    types = {_infer_value_type(value) for value in values if value is not None}
    if not types:
        return "text"
    if len(types) > 1:
        return "mixed"
    return next(iter(types))


def _score_sheet(rows: list[list], sheet_name: str) -> SheetProfile:
    if not rows:
        return SheetProfile(
            sheet_name=sheet_name,
            confidence=0.0,
            warnings=["Empty sheet"],
            row_count=0,
            column_count=0,
            header_row_index=None,
        )

    column_count = max(len(row) for row in rows)
    header = rows[0]
    header_like = all(not isinstance(value, (int, float, bool)) for value in header if value is not None)
    data_rows = rows[1:] if header_like else rows
    confidence = min(1.0, 0.25 + min(len(rows) / 100, 0.5) + (0.25 if header_like else 0.0))
    if sheet_name == "Sheet1":
        confidence = max(0.0, confidence - 0.15)
    return SheetProfile(
        sheet_name=sheet_name,
        confidence=confidence,
        warnings=[],
        row_count=len(rows),
        data_row_count=len(data_rows),
        column_count=column_count,
        header_row_index=0 if header_like else None,
        preview_columns=[str(value) for value in header] if header_like else [],
        preview_rows=[list(row) for row in data_rows[:10]],
    )


def _infer_column_name_from_header(header: object, index: int) -> str:
    if header in (None, ""):
        return f"column_{index + 1}"
    return str(header).strip().lower().replace(" ", "_")


def _profile_columns(rows: list[list], header: list[object]) -> list[ColumnProfile]:
    profiles: list[ColumnProfile] = []
    for index, header_value in enumerate(header):
        column_values = [row[index] for row in rows if index < len(row)]
        non_null_values = [value for value in column_values if value not in (None, "")]
        profiles.append(
            ColumnProfile(
                column_name=_infer_column_name_from_header(header_value, index),
                detected_type=_infer_type_from_values(non_null_values),
                non_null_count=len(non_null_values),
                sample_values=non_null_values[:3],
                confidence=1.0 if non_null_values else 0.0,
                warnings=[],
            )
        )
    return profiles


def _build_warnings(sheet_profile: SheetProfile) -> list[str]:
    warnings = list(sheet_profile.warnings)
    if sheet_profile.header_row_index is None:
        warnings.append("Header row not detected")
    return warnings


def generate_profile(upload_id: str, storage_path, repo=None) -> WorkbookProfile:
    from ingestion.sources.xlsx import read_workbook

    sheets = []
    for sheet in read_workbook(storage_path):
        sheets.append(SheetProfile(upload_id=upload_id, **sheet))
    profile = WorkbookProfile(sheets=sheets, metadata={"upload_id": upload_id})
    if repo is not None and hasattr(repo, "save_upload_profile"):
        repo.save_upload_profile(upload_id, profile)
    return profile

