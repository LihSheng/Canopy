from datetime import datetime

from v3.ingestion.domain import SheetProfile, ColumnProfile
from v3.ingestion.profiling import _score_sheet, _infer_type_from_values, _infer_value_type


class TestSheetScoring:
    def test_high_confidence_with_header_and_many_rows(self):
        rows = [["Name", "Age"], ["Alice", 30], ["Bob", 25]] * 30
        profile = _score_sheet(rows, "DataSheet")
        assert profile.confidence > 0.5
        assert profile.header_row_index == 0

    def test_low_confidence_for_empty_sheet(self):
        profile = _score_sheet([], "EmptySheet")
        assert profile.confidence == 0.0
        assert "Empty sheet" in profile.warnings

    def test_sheet1_penalty(self):
        rows = [["Name"], ["Alice"]]
        sheet1 = _score_sheet(rows, "Sheet1")
        data = _score_sheet(rows, "Data")
        assert sheet1.confidence < data.confidence

    def test_no_header_if_numbers(self):
        rows = [[1, 2], [3, 4]]
        profile = _score_sheet(rows, "Data")
        assert profile.header_row_index is None

    def test_column_count_matches_max(self):
        rows = [["A", "B", "C"], [1, 2, 3]]
        profile = _score_sheet(rows, "Data")
        assert profile.column_count == 3


class TestTypeInference:
    def test_infers_number(self):
        assert _infer_value_type(42) == "number"
        assert _infer_value_type(3.14) == "number"

    def test_infers_text(self):
        assert _infer_value_type("hello") == "text"

    def test_infers_boolean(self):
        assert _infer_value_type(True) == "boolean"
        assert _infer_value_type(False) == "boolean"

    def test_infers_date_from_string(self):
        assert _infer_value_type("2026-01-15") == "date"

    def test_infers_date_from_datetime(self):
        assert _infer_value_type(datetime(2026, 1, 15)) == "date"

    def test_null_returns_null(self):
        assert _infer_value_type(None) == "null"

    def test_mixed_types_detected(self):
        values = [1, "hello", 2]
        assert _infer_type_from_values(values) == "mixed"

    def test_single_type_stays(self):
        values = [1, 2, 3]
        assert _infer_type_from_values(values) == "number"

    def test_all_null_falls_to_text(self):
        values = [None, None]
        assert _infer_type_from_values(values) == "text"

    def test_boolean_detected(self):
        values = [True, False, True]
        assert _infer_type_from_values(values) == "boolean"
