from pathlib import Path

import openpyxl


def read_workbook(path: str | Path) -> list[dict]:
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    sheets = []
    for sheet_name in wb.sheetnames:
        ws = wb[sheet_name]
        rows = list(ws.iter_rows(values_only=True))
        sheets.append({"sheet_name": sheet_name, "rows": rows})
    wb.close()
    return sheets


def sample_rows(rows: list, max_samples: int = 20) -> list:
    if not rows:
        return []
    if len(rows) <= max_samples:
        return rows
    return rows[:max_samples]
