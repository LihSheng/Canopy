import pytest

pytestmark = pytest.mark.business_rule

from insights.parser import parse_llm_response


class TestResponseParser:
    def test_parses_valid_json(self):
        raw = (
            '{\n'
            '  "summary": "Spend was stable this month.",\n'
            '  "recommendations": ["Review claims.", "Monitor payroll."],\n'
            '  "key_findings": ["Payroll dominates spend.", "No anomalies detected."]\n'
            '}'
        )
        result = parse_llm_response(raw)

        assert result.summary == "Spend was stable this month."
        assert len(result.recommendations) == 2
        assert len(result.key_findings) == 2
        assert result.recommendations[0] == "Review claims."
        assert result.key_findings[0] == "Payroll dominates spend."

    def test_returns_empty_on_invalid_json(self):
        raw = "Not valid JSON at all"
        result = parse_llm_response(raw)

        assert result.summary == ""
        assert result.recommendations == []
        assert result.key_findings == []

    def test_returns_empty_on_empty_string(self):
        raw = ""
        result = parse_llm_response(raw)

        assert result.summary == ""
        assert result.recommendations == []
        assert result.key_findings == []

    def test_strips_markdown_code_block(self):
        raw = (
            '```json\n'
            '{"summary": "Stable.", "recommendations": ["R1"], '
            '"key_findings": ["F1"]}\n'
            '```'
        )
        result = parse_llm_response(raw)

        assert result.summary == "Stable."

    def test_strips_markdown_without_language_tag(self):
        raw = (
            '```\n'
            '{"summary": "Stable.", "recommendations": ["R1"], '
            '"key_findings": ["F1"]}\n'
            '```'
        )
        result = parse_llm_response(raw)

        assert result.summary == "Stable."

    def test_handles_missing_keys(self):
        raw = '{"summary": "Only summary."}'
        result = parse_llm_response(raw)

        assert result.summary == "Only summary."
        assert result.recommendations == []
        assert result.key_findings == []

    def test_filters_empty_strings_from_lists(self):
        raw = (
            '{"summary": "Text.", '
            '"recommendations": ["", "Valid", ""], '
            '"key_findings": ["", ""]}'
        )
        result = parse_llm_response(raw)

        assert result.recommendations == ["Valid"]
        assert result.key_findings == []

    def test_handles_non_string_list_items(self):
        raw = (
            '{"summary": "Text.", '
            '"recommendations": [123, true], '
            '"key_findings": [null, "F1"]}'
        )
        result = parse_llm_response(raw)

        assert "123" in result.recommendations
        assert "F1" in result.key_findings


class TestGeneratedInsightModel:
    """Cover GeneratedInsightModel.pack_list and unpack_list edge cases.

    Lines 50-51: JSONDecodeError / TypeError -> empty list.
    """

    def test_pack_unpack_roundtrip(self):
        from insights.schema import GeneratedInsightModel

        items = ["Review claims", "Check payroll"]
        packed = GeneratedInsightModel.pack_list(items)
        unpacked = GeneratedInsightModel.unpack_list(packed)
        assert unpacked == items

    def test_unpack_list_invalid_json(self):
        """line 50-51: JSONDecodeError returns empty list."""
        from insights.schema import GeneratedInsightModel

        result = GeneratedInsightModel.unpack_list("not-json")
        assert result == []

    def test_unpack_list_type_error(self):
        """line 50-51: TypeError returns empty list."""
        from insights.schema import GeneratedInsightModel

        result = GeneratedInsightModel.unpack_list(None)
        assert result == []

    def test_unpack_list_empty_default(self):
        from insights.schema import GeneratedInsightModel

        result = GeneratedInsightModel.unpack_list("[]")
        assert result == []
