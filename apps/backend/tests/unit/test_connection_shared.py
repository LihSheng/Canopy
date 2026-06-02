"""Tests for connection/_shared.py utilities, especially JSONL serialization type preservation."""

import json
import tempfile
from datetime import UTC, date, datetime, time
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from connection._shared import _json_default, is_empty_row, normalize_header, write_jsonl_version


class TestJsonDefault:
    def test_datetime_serializes_to_iso(self):
        dt = datetime(2024, 6, 15, 14, 30, 0, tzinfo=UTC)
        result = _json_default(dt)
        assert "2024-06-15" in result
        assert "14:30" in result

    def test_date_serializes_to_iso(self):
        d = date(2024, 6, 15)
        result = _json_default(d)
        assert result == "2024-06-15"

    def test_time_serializes_to_iso(self):
        t = time(14, 30, 0)
        result = _json_default(t)
        assert "14:30" in result

    def test_decimal_serializes_to_string_repr(self):
        d = Decimal("123.45")
        result = _json_default(d)
        assert result == "123.45"

    def test_uuid_serializes_to_string(self):
        u = UUID("550e8400-e29b-41d4-a716-446655440000")
        result = _json_default(u)
        assert result == "550e8400-e29b-41d4-a716-446655440000"

    def test_bytes_serializes_to_hex(self):
        b = b"hello"
        result = _json_default(b)
        assert result == "68656c6c6f"

    def test_set_serializes_to_sorted_list(self):
        s = {"z", "a", "m"}
        result = _json_default(s)
        assert result == ["a", "m", "z"]

    def test_int_falls_through_json_no_default_needed(self):
        """int is natively JSON-serializable so _json_default is not called."""
        result = json.dumps(42)
        assert result == "42"

    def test_float_falls_through_json_no_default_needed(self):
        """float is natively JSON-serializable so _json_default is not called."""
        result = json.dumps(3.14)
        assert result == "3.14"

    def test_bool_falls_through_json_no_default_needed(self):
        """bool is natively JSON-serializable so _json_default is not called."""
        result = json.dumps(True)
        assert result == "true"

    def test_none_falls_through_json_no_default_needed(self):
        """None is natively JSON-serializable so _json_default is not called."""
        result = json.dumps(None)
        assert result == "null"

    def test_str_falls_through_json_no_default_needed(self):
        """str is natively JSON-serializable so _json_default is not called."""
        result = json.dumps("hello")
        assert result == '"hello"'

    def test_int_preserved_in_roundtrip(self):
        """int values round-trip through json.dumps/loads correctly."""
        data = {"value": 42}
        serialized = json.dumps(data, default=_json_default)
        loaded = json.loads(serialized)
        assert loaded["value"] == 42
        assert type(loaded["value"]) is int

    def test_float_preserved_in_roundtrip(self):
        """float values round-trip through json.dumps/loads correctly."""
        data = {"value": 3.14}
        serialized = json.dumps(data, default=_json_default)
        loaded = json.loads(serialized)
        assert loaded["value"] == 3.14
        assert type(loaded["value"]) is float

    def test_bool_preserved_in_roundtrip(self):
        """bool values round-trip through json.dumps/loads correctly."""
        data = {"value": True}
        serialized = json.dumps(data, default=_json_default)
        loaded = json.loads(serialized)
        assert loaded["value"] is True
        assert type(loaded["value"]) is bool

    def test_none_preserved_in_roundtrip(self):
        """None values round-trip through json.dumps/loads correctly."""
        data = {"value": None}
        serialized = json.dumps(data, default=_json_default)
        loaded = json.loads(serialized)
        assert loaded["value"] is None

    def test_decimal_roundtrips_as_string_no_precision_loss(self):
        """Decimal with high precision round-trips as string (no float precision loss)."""
        data = {"price": Decimal("123456789.123456789")}
        serialized = json.dumps(data, default=_json_default)
        loaded = json.loads(serialized)
        assert loaded["price"] == "123456789.123456789"

    def test_datetime_roundtrips_as_iso_string(self):
        data = {"created": datetime(2024, 6, 15, 14, 30, 0, tzinfo=UTC)}
        serialized = json.dumps(data, default=_json_default)
        loaded = json.loads(serialized)
        assert "2024-06-15" in loaded["created"]

    def test_mixed_row_roundtrip_preserves_native_types(self):
        """A realistic DB row with mixed types preserves int/float/bool/None/str."""
        row = {
            "id": 1,
            "name": "Alice",
            "salary": 75000.50,
            "active": True,
            "end_date": None,
            "created_at": datetime(2024, 1, 1, tzinfo=UTC),
            "bonus": Decimal("5000.00"),
        }
        serialized = json.dumps(row, default=_json_default)
        loaded = json.loads(serialized)
        assert type(loaded["id"]) is int
        assert loaded["id"] == 1
        assert type(loaded["name"]) is str
        assert loaded["name"] == "Alice"
        assert type(loaded["salary"]) is float
        assert loaded["salary"] == 75000.50
        assert type(loaded["active"]) is bool
        assert loaded["active"] is True
        assert loaded["end_date"] is None
        # datetime and Decimal become strings (acceptable for JSONL)
        assert type(loaded["created_at"]) is str
        assert type(loaded["bonus"]) is str


class TestWriteJsonlVersion:
    def test_writes_valid_jsonl_file(self):
        rows = [
            {"id": 1, "name": "Alice"},
            {"id": 2, "name": "Bob"},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            import connection._shared as mod

            _original_storage_root = mod.storage_root
            try:
                mod.storage_root = lambda: Path(tmpdir)
                path = write_jsonl_version(rows, "test-dataset", "employees")
                assert path.exists()
                lines = path.read_text().strip().split("\n")
                assert len(lines) == 2
                loaded1 = json.loads(lines[0])
                loaded2 = json.loads(lines[1])
                assert loaded1["id"] == 1
                assert loaded2["name"] == "Bob"
            finally:
                mod.storage_root = _original_storage_root

    def test_int_and_float_preserved_in_jsonl(self):
        rows = [
            {"id": 1, "score": 95.5},
            {"id": 2, "score": 87.3},
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            import connection._shared as mod

            _original_storage_root = mod.storage_root
            try:
                mod.storage_root = lambda: Path(tmpdir)
                path = write_jsonl_version(rows, "test-dataset", "scores")
                lines = path.read_text().strip().split("\n")
                loaded1 = json.loads(lines[0])
                assert type(loaded1["id"]) is int
                assert type(loaded1["score"]) is float
            finally:
                mod.storage_root = _original_storage_root


class TestIsEmptyRow:
    def test_all_none_is_empty(self):
        assert is_empty_row([None, None, None])

    def test_all_empty_string_is_empty(self):
        assert is_empty_row(["", ""])

    def test_mixed_none_and_empty_is_empty(self):
        assert is_empty_row([None, "", None])

    def test_one_value_is_not_empty(self):
        assert not is_empty_row([None, "hello", None])

    def test_zero_is_not_empty(self):
        assert not is_empty_row([0])

    def test_empty_list_is_empty(self):
        assert is_empty_row([])


class TestNormalizeHeader:
    def test_replaces_none_with_column_n(self):
        result = normalize_header(["Name", None, "Age"], 3)
        assert result == ["Name", "column_2", "Age"]

    def test_replaces_empty_string_with_column_n(self):
        result = normalize_header(["", "Name", ""], 3)
        assert result == ["column_1", "Name", "column_3"]

    def test_all_valid_headers_pass_through(self):
        result = normalize_header(["id", "name", "email"], 3)
        assert result == ["id", "name", "email"]

    def test_handles_extra_column_count(self):
        """When column_count > len(values), remaining columns get numbered."""
        result = normalize_header(["Name"], 3)
        assert result == ["Name", "column_2", "column_3"]
