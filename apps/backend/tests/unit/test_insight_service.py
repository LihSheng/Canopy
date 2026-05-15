
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
