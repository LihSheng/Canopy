from datetime import datetime

from v3.ingestion.domain import ColumnProfile, SheetProfile, UploadStatus, WorkbookProfile
from v3.ingestion.repository import IngestionRepository
from v3.ingestion.sources.xlsx import read_workbook, sample_rows
from common.errors import AppError

_DATE_FORMATS = [
    "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d",
    "%Y-%m-%d %H:%M:%S", "%d-%b-%Y", "%b %d %Y",
]


def _infer_value_type(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, datetime):
        return "date"
    s = str(value).strip()
    if not s:
        return "null"
    for fmt in _DATE_FORMATS:
        try:
            datetime.strptime(s, fmt)
            return "date"
        except ValueError:
            pass
    return "text"


def _score_sheet(rows: list, sheet_name: str) -> SheetProfile:
    warnings_list: list[str] = []
    if not rows:
        return SheetProfile(sheet_name=sheet_name, row_count=0, column_count=0, header_row_index=None, confidence=0.0, warnings=["Empty sheet"])

    col_count = max(len(r) for r in rows) if rows else 0
    data_rows = rows

    first = rows[0]
    all_strings = all(isinstance(c, str) for c in first if c is not None)
    has_header = all_strings and len([c for c in first if c is not None]) > 0

    header_index = 0 if has_header else None
    if has_header:
        data_rows = rows[1:]

    non_empty = [r for r in data_rows if any(c is not None for c in r)]
    row_count = len(non_empty)

    confidence = 0.0
    if has_header:
        confidence += 0.3
    confidence += min(row_count / 50, 0.4)
    confidence += min(col_count / 10, 0.2)
    if sheet_name.lower() in ("sheet1", "sheet2", "sheet3"):
        confidence -= 0.1
    confidence = max(0.0, min(1.0, confidence))

    return SheetProfile(
        sheet_name=sheet_name,
        row_count=row_count,
        column_count=col_count,
        header_row_index=header_index,
        confidence=round(confidence, 2),
        warnings=warnings_list,
    )


def _infer_type_from_values(values: list) -> str:
    types_seen: set[str] = set()
    for v in values:
        t = _infer_value_type(v)
        if t != "null":
            types_seen.add(t)
    if len(types_seen) == 0:
        return "text"
    if len(types_seen) == 1:
        return types_seen.pop()
    if types_seen == {"number", "text"}:
        return "mixed"
    if types_seen == {"date", "text"}:
        return "mixed"
    return "mixed"


def _infer_column_name_from_header(header: str) -> str | None:
    cleaned = header.strip().lower().replace(" ", "_").replace("-", "_")
    known = {
        "employee_id", "employee_name", "name", "full_name", "department",
        "dept", "amount", "salary", "pay", "payroll", "currency", "date",
        "submitted_at", "period", "claim_type", "status", "email",
    }
    if cleaned in known:
        return cleaned
    if "id" in cleaned or "code" in cleaned:
        return cleaned
    return None


def _profile_columns(header_row: list | None, data_rows: list) -> list[ColumnProfile]:
    if not data_rows:
        return []
    col_count = max(len(r) for r in data_rows)
    columns: list[ColumnProfile] = []

    for i in range(col_count):
        col_values = [r[i] for r in data_rows if i < len(r)]
        sample = col_values[:5]
        non_null = [v for v in col_values if v is not None]
        null_ratio = round(1 - (len(non_null) / max(len(col_values), 1)), 2)

        inferred = _infer_type_from_values(col_values)
        confidence = 0.8 if inferred != "mixed" else 0.4
        source_name = str(header_row[i]) if header_row and i < len(header_row) else f"Column {i + 1}"
        suggested = _infer_column_name_from_header(source_name) if header_row else None

        columns.append(ColumnProfile(
            source_column_name=source_name,
            inferred_type=inferred,
            sample_values=[str(v) for v in sample if v is not None],
            null_ratio=null_ratio,
            confidence=confidence,
            suggested_target_field=suggested,
        ))
    return columns


def _build_warnings(sheet_profile: SheetProfile, column_profiles: list[ColumnProfile]) -> list[str]:
    warnings: list[str] = []
    for col in column_profiles:
        if col.confidence < 0.5:
            warnings.append(f"Low confidence column: '{col.source_column_name}'")
        if col.null_ratio > 0.5:
            warnings.append(f"Many null values in column: '{col.source_column_name}'")
    if sheet_profile.confidence < 0.4:
        warnings.append(f"Best sheet '{sheet_profile.sheet_name}' has low confidence")
    return warnings


def generate_profile(repo: IngestionRepository, upload_id: str) -> WorkbookProfile:
    record = repo.get_upload(upload_id)
    if record is None:
        from common.errors import NotFoundError
        raise NotFoundError("Upload not found")

    if record.status == "failed":
        from common.errors import ValidationError
        raise ValidationError(f"Cannot profile upload in status '{record.status}'")

    paths = read_workbook(record.storage_path)
    all_sheet_profiles = [_score_sheet(s["rows"], s["sheet_name"]) for s in paths]

    data_sheets = [s for s in all_sheet_profiles if s.row_count > 0]
    if not data_sheets:
        raise AppError("No usable data sheets found in workbook", 400)

    data_sheets.sort(key=lambda s: s.confidence, reverse=True)
    best = data_sheets[0]
    best_raw = next(s for s in paths if s["sheet_name"] == best.sheet_name)

    header_row = best_raw["rows"][0] if best.header_row_index is not None else None
    data_rows_raw = best_raw["rows"][1:] if best.header_row_index is not None else best_raw["rows"]
    sampled = sample_rows(data_rows_raw, 20)
    columns = _profile_columns(header_row, sampled)
    preview_data = []
    for r in sampled:
        preview_data.append([str(c) if c is not None else None for c in r])
    warnings = _build_warnings(best, columns)

    repo.update_status(upload_id, UploadStatus.profiled)

    return WorkbookProfile(
        upload_id=upload_id,
        best_sheet_name=best.sheet_name,
        sheet_profiles=all_sheet_profiles,
        column_profiles=columns,
        preview_rows=preview_data,
        warnings=warnings,
    )
