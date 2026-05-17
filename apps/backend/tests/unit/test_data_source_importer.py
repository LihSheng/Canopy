from __future__ import annotations

import io
from types import SimpleNamespace

import openpyxl

from common.config import settings
from v4.connection.importer import build_sheet_profiles, materialize_dataset_version, save_uploaded_file


def _make_xlsx() -> bytes:
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.title = "Payroll"
    sheet.append(["name", "amount"])
    sheet.append(["Alice", 100])
    sheet.append(["Bob", 200])

    notes = workbook.create_sheet("Notes")
    notes.append(["comment"])

    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def test_save_uploaded_file_and_build_profiles(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)
    upload = SimpleNamespace(filename="sample.xlsx", file=io.BytesIO(_make_xlsx()))

    storage_path = save_uploaded_file(upload)

    assert storage_path.exists()
    assert storage_path.suffix == ".xlsx"

    profiles = build_sheet_profiles(storage_path)
    assert [profile["sheet_name"] for profile in profiles] == ["Payroll", "Notes"]
    assert profiles[0]["row_count"] == 3
    assert profiles[0]["data_row_count"] == 2
    assert profiles[0]["column_count"] == 2
    assert profiles[0]["header_row_index"] == 0
    assert profiles[0]["preview_columns"] == ["name", "amount"]
    assert profiles[0]["preview_rows"][0] == ["Alice", 100]


def test_materialize_dataset_version_writes_jsonl(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "export_storage_dir", str(tmp_path), raising=False)
    upload = SimpleNamespace(filename="sample.xlsx", file=io.BytesIO(_make_xlsx()))
    storage_path = save_uploaded_file(upload)

    version_path, row_count, column_count = materialize_dataset_version(storage_path, "Payroll", "dataset-1")

    assert version_path.exists()
    assert row_count == 2
    assert column_count == 2

    rows = version_path.read_text(encoding="utf-8").splitlines()
    assert rows[0] == '{"name": "Alice", "amount": 100}'
    assert rows[1] == '{"name": "Bob", "amount": 200}'
