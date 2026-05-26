import pytest

from dataset.cleaning import clean_rows


@pytest.fixture(autouse=True)
def _setup_db():
    """Module isolation only; no database setup needed here."""
    yield


class TestCleanRows:
    def test_trims_whitespace_from_strings(self):
        rows = [{"name": "  Alice  ", "age": "30"}]
        result = clean_rows(rows)
        assert result["cleaned_rows"][0]["name"] == "Alice"

    def test_trims_trailing_newlines(self):
        rows = [{"name": "Bob\n", "city": "\tNYC\t"}]
        result = clean_rows(rows)
        assert result["cleaned_rows"][0]["name"] == "Bob"
        assert result["cleaned_rows"][0]["city"] == "NYC"

    def test_normalizes_headers_spaces_to_underscores(self):
        rows = [{"First Name": "Alice", "Last Name": "Chen"}]
        result = clean_rows(rows)
        columns = result["columns"]
        assert "first_name" in columns
        assert "last_name" in columns

    def test_normalizes_headers_lowercase(self):
        rows = [{"FullName": "Alice"}]
        result = clean_rows(rows)
        assert "fullname" in result["columns"]

    def test_normalizes_headers_dedup(self):
        rows = [{"name": "Alice", "Name": "Bob"}]
        result = clean_rows(rows)
        columns = result["columns"]
        assert "name" in columns
        assert "name_2" in columns

    def test_normalizes_headers_strips_underscores(self):
        rows = [{" _name_": "Alice"}]
        result = clean_rows(rows)
        assert result["columns"][0] == "name"

    def test_removes_fully_empty_rows(self):
        rows = [{"name": "Alice"}, {"name": None, "age": None}, {"name": "Bob"}]
        result = clean_rows(rows)
        assert result["row_count"] == 2

    def test_removes_multiple_empty_rows(self):
        rows = [{"col": None}, {"col": ""}, {"col": "val"}]
        result = clean_rows(rows)
        assert result["row_count"] == 1

    def test_infers_column_types_number_from_integers(self):
        rows = [{"amount": "100"}, {"amount": "200"}]
        result = clean_rows(rows)
        assert result["column_types"]["amount"] == "number"

    def test_infers_column_types_number_from_floats(self):
        rows = [{"price": "1.50"}, {"price": "2.99"}]
        result = clean_rows(rows)
        assert result["column_types"]["price"] == "number"

    def test_infers_column_types_text(self):
        rows = [{"desc": "hello"}, {"desc": "world"}]
        result = clean_rows(rows)
        assert result["column_types"]["desc"] == "text"

    def test_infers_column_types_date(self):
        rows = [{"dt": "2024-01-15"}, {"dt": "2024-02-20"}]
        result = clean_rows(rows)
        assert result["column_types"]["dt"] == "date"

    def test_infers_column_types_date_dd_mm_yyyy(self):
        rows = [{"dt": "15/01/2024"}, {"dt": "20/02/2024"}]
        result = clean_rows(rows)
        assert result["column_types"]["dt"] == "date"

    def test_infers_column_types_boolean(self):
        rows = [{"flag": "true"}, {"flag": "false"}]
        result = clean_rows(rows)
        assert result["column_types"]["flag"] == "boolean"

    def test_infers_column_types_boolean_yes_no(self):
        rows = [{"flag": "yes"}, {"flag": "no"}]
        result = clean_rows(rows)
        assert result["column_types"]["flag"] == "boolean"

    def test_infers_column_types_one_zero_as_number_not_boolean(self):
        rows = [{"flag": "1"}, {"flag": "0"}]
        result = clean_rows(rows)
        assert result["column_types"]["flag"] == "number"

    def test_flags_invalid_cells_in_number_column(self):
        rows = [{"amount": "100"}, {"amount": "abc"}]
        result = clean_rows(rows)
        issues = result["issues"]
        assert any(i["type"] == "invalid_cell" and i["column"] == "amount" for i in issues)

    def test_flags_invalid_cells_in_date_column(self):
        rows = [{"dt": "2024-01-15"}, {"dt": "not-a-date"}]
        result = clean_rows(rows)
        issues = result["issues"]
        assert any(i["type"] == "invalid_cell" and i["column"] == "dt" and i["expected_type"] == "date" for i in issues)

    def test_flags_invalid_cells_in_boolean_column(self):
        rows = [{"flag": "true"}, {"flag": "maybe"}]
        result = clean_rows(rows)
        issues = result["issues"]
        assert any(
            i["type"] == "invalid_cell" and i["column"] == "flag" and i["expected_type"] == "boolean" for i in issues
        )

    def test_empty_input_returns_empty_result(self):
        result = clean_rows([])
        assert result["row_count"] == 0
        assert result["column_count"] == 0
        assert result["cleaned_rows"] == []
        assert result["columns"] == []
        assert result["issues"] == []
        assert result["column_types"] == {}

    def test_column_types_returned_correctly_for_mixed(self):
        rows = [
            {"id": "1", "name": "Alice", "active": "true", "hired": "2024-01-01"},
            {"id": "2", "name": "Bob", "active": "false", "hired": "2024-02-01"},
        ]
        result = clean_rows(rows)
        types = result["column_types"]
        assert types["id"] == "number"
        assert types["name"] == "text"
        assert types["active"] == "boolean"
        assert types["hired"] == "date"

    def test_row_count_and_column_count_are_correct(self):
        rows = [
            {"a": "1", "b": "x"},
            {"a": "2", "b": "y"},
            {"a": "3", "b": "z"},
        ]
        result = clean_rows(rows)
        assert result["row_count"] == 3
        assert result["column_count"] == 2

    def test_column_types_keys_use_normalized_names(self):
        rows = [{"First Name": "Alice", "Last Name": "Chen"}]
        result = clean_rows(rows)
        types = result["column_types"]
        assert "first_name" in types
        assert "last_name" in types

    def test_does_not_flag_none_values(self):
        rows = [{"amount": "100"}, {"amount": None}]
        result = clean_rows(rows)
        issues = result["issues"]
        invalid = [i for i in issues if i["type"] == "invalid_cell"]
        assert len(invalid) == 0
