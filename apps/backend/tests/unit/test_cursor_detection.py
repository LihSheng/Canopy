"""Tests for cursor column auto-detection service."""
import pytest

from connection.cursor_detection import detect_cursor_column


class TestDetectCursorColumn:
    def test_updated_at_is_highest_priority(self):
        columns = [
            {"name": "id", "data_type": "bigint"},
            {"name": "created_at", "data_type": "timestamp"},
            {"name": "updated_at", "data_type": "timestamp"},
        ]
        assert detect_cursor_column(columns) == "updated_at"

    def test_last_modified_at_when_no_updated_at(self):
        columns = [
            {"name": "id", "data_type": "bigint"},
            {"name": "last_modified_at", "data_type": "timestamptz"},
            {"name": "created_at", "data_type": "timestamp"},
        ]
        assert detect_cursor_column(columns) == "last_modified_at"

    def test_created_at_when_no_better_match(self):
        columns = [
            {"name": "id", "data_type": "bigint"},
            {"name": "created_at", "data_type": "timestamp"},
        ]
        assert detect_cursor_column(columns) == "created_at"

    def test_returns_none_when_no_timestamp_columns(self):
        columns = [
            {"name": "id", "data_type": "bigint"},
            {"name": "name", "data_type": "varchar"},
        ]
        assert detect_cursor_column(columns) is None

    def test_returns_none_for_empty_list(self):
        assert detect_cursor_column([]) is None

    def test_matches_based_on_name_not_position(self):
        columns = [
            {"name": "first", "data_type": "timestamp"},
            {"name": "updated_at", "data_type": "timestamptz"},
            {"name": "last", "data_type": "timestamp"},
        ]
        assert detect_cursor_column(columns) == "updated_at"

    def test_handles_various_timestamp_type_names(self):
        for ts_type in ("timestamp", "timestamptz", "timestamp without time zone",
                        "timestamp with time zone", "datetime", "date"):
            columns = [
                {"name": "updated_at", "data_type": ts_type},
            ]
            assert detect_cursor_column(columns) == "updated_at", f"failed for {ts_type}"
