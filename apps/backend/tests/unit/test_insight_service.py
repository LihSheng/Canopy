import pytest

pytestmark = pytest.mark.business_rule

from insights.service import generate_insight


class _FakeLlmClient:
    def __init__(self, response_text: str):
        self._response = response_text
        self.call_count = 0

    def generate(self, prompt: str) -> str:
        self.call_count += 1
        return self._response


def _valid_llm_response() -> str:
    return (
        '{"summary": "Spend was stable this month.", '
        '"recommendations": ["Review claims.", "Monitor payroll."], '
        '"key_findings": ["Payroll dominates spend.", "No anomalies detected."]}'
    )


class TestInsightService:
    def test_generates_insight_with_valid_llm_response(self, seed_analytics_data):
        db = seed_analytics_data
        client = _FakeLlmClient(_valid_llm_response())

        result = generate_insight(db, llm=client)

        assert result is not None
        assert result.summary_text == "Spend was stable this month."
        assert result.is_fallback is False
        assert len(result.recommendations) == 2
        assert len(result.key_findings) == 2
        assert result.snapshot_id != ""
        assert result.generated_at != ""

    def test_uses_fallback_when_llm_fails(self, seed_analytics_data):
        db = seed_analytics_data

        class FailClient:
            def generate(self, prompt: str) -> str:
                raise RuntimeError("LLM unavailable")

        result = generate_insight(db, llm=FailClient())

        assert result is not None
        assert result.is_fallback is True
        assert result.summary_text != ""
        assert len(result.recommendations) > 0
        assert len(result.key_findings) > 0

    def test_uses_fallback_when_llm_returns_unparseable(self, seed_analytics_data):
        db = seed_analytics_data
        client = _FakeLlmClient("not valid json {{{")

        result = generate_insight(db, llm=client)

        assert result is not None
        assert result.is_fallback is True

    def test_uses_fallback_when_parsed_summary_empty(self, seed_analytics_data):
        db = seed_analytics_data
        client = _FakeLlmClient(
            '{"summary": "", "recommendations": [], "key_findings": []}'
        )

        result = generate_insight(db, llm=client)

        assert result is not None
        assert result.is_fallback is True

    def test_returns_none_when_no_cache(self, db_session):
        result = generate_insight(db_session)

        assert result is None

    def test_stores_provenance_metadata(self, seed_analytics_data):
        db = seed_analytics_data
        client = _FakeLlmClient(_valid_llm_response())

        result = generate_insight(db, llm=client)

        assert result is not None
        assert result.snapshot_id != ""
        assert result.generated_at != ""
        assert result.current_month != ""
        assert result.department_count > 0
        assert result.anomaly_count >= 0
        assert result.total_payroll > 0
        assert result.total_claims > 0

    def test_fallback_summary_references_same_snapshot(self, seed_analytics_data):
        db = seed_analytics_data

        class FailClient:
            def generate(self, prompt: str) -> str:
                raise RuntimeError("unavailable")

        result = generate_insight(db, llm=FailClient())

        assert result is not None
        assert result.snapshot_id != ""


class TestResolveGeneratedAt:
    """Cover _resolve_generated_at edge cases (lines 9-17)."""

    def test_datetime_input_returns_asis(self):
        from datetime import UTC, datetime
        from insights.repository import _resolve_generated_at

        now = datetime.now(UTC)
        result = _resolve_generated_at(now)
        assert result == now

    def test_valid_iso_string_parsed(self):
        from datetime import UTC, datetime
        from insights.repository import _resolve_generated_at

        result = _resolve_generated_at("2026-05-15T10:00:00+00:00")
        assert result.year == 2026
        assert result.month == 5

    def test_invalid_string_falls_back_to_now(self):
        """lines 15-16: ValueError -> datetime.now(UTC)."""
        from datetime import UTC, datetime
        from insights.repository import _resolve_generated_at

        result = _resolve_generated_at("not-a-date")
        assert isinstance(result, datetime)

    def test_empty_string_falls_back_to_now(self):
        """line 17: empty val -> datetime.now(UTC)."""
        from datetime import UTC, datetime
        from insights.repository import _resolve_generated_at

        result = _resolve_generated_at("")
        assert isinstance(result, datetime)
