from __future__ import annotations

import json

from dataset.preview_service import read_dataset_preview


def _write_jsonl(tmp_path, rows: list[dict]) -> str:
    path = tmp_path / "data.jsonl"
    with open(str(path), "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")
    return str(path)


def test_read_jsonl_basic(tmp_path):
    rows = [
        {"name": "Alice", "amount": 100},
        {"name": "Bob", "amount": 200},
    ]
    storage_path = _write_jsonl(tmp_path, rows)

    result = read_dataset_preview(storage_path)

    assert result["columns"] == ["name", "amount"]
    assert result["rows"] == [["Alice", 100], ["Bob", 200]]
    assert result["total_row_count"] == 2
    assert result["filtered_row_count"] == 2
    assert result["page"] == 1
    assert result["page_size"] == 100


def test_read_jsonl_pagination(tmp_path):
    rows = [{"id": i, "val": f"row{i}"} for i in range(5)]
    storage_path = _write_jsonl(tmp_path, rows)

    page1 = read_dataset_preview(storage_path, page=1, page_size=2)
    assert page1["rows"] == [[0, "row0"], [1, "row1"]]
    assert page1["total_row_count"] == 5
    assert page1["filtered_row_count"] == 5

    page2 = read_dataset_preview(storage_path, page=2, page_size=2)
    assert page2["rows"] == [[2, "row2"], [3, "row3"]]
    assert page2["total_row_count"] == 5

    page3 = read_dataset_preview(storage_path, page=3, page_size=2)
    assert page3["rows"] == [[4, "row4"]]
    assert page3["total_row_count"] == 5

    page4 = read_dataset_preview(storage_path, page=4, page_size=2)
    assert page4["rows"] == []
    assert page4["total_row_count"] == 5


def test_read_jsonl_search(tmp_path):
    rows = [
        {"id": 1, "name": "Bob"},
        {"id": 2, "name": "Charlie"},
        {"id": 3, "name": "Alice"},
        {"id": 4, "name": "David"},
        {"id": 5, "name": "Eve"},
    ]
    storage_path = _write_jsonl(tmp_path, rows)

    result = read_dataset_preview(storage_path, search="alice")

    assert result["total_row_count"] == 5
    assert result["filtered_row_count"] == 1
    assert result["rows"] == [[3, "Alice"]]


def test_read_jsonl_search_no_match(tmp_path):
    rows = [
        {"name": "Alice", "amount": 100},
        {"name": "Bob", "amount": 200},
    ]
    storage_path = _write_jsonl(tmp_path, rows)

    result = read_dataset_preview(storage_path, search="zzzzzzNotFound")

    assert result["total_row_count"] == 2
    assert result["filtered_row_count"] == 0
    assert result["rows"] == []


def test_read_jsonl_missing_file():
    result = read_dataset_preview("/nonexistent/path/data.jsonl")

    assert result["columns"] == []
    assert result["rows"] == []
    assert result["total_row_count"] == 0
    assert result["filtered_row_count"] == 0
    assert result["page"] == 1
    assert result["page_size"] == 100

