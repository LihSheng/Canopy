from unittest.mock import MagicMock, patch

from insights.domain import FactBundle
from insights.facts import extract_facts


class TestFactExtraction:
    def test_returns_none_when_no_cache(self, db_session):
        with patch(
            "insights.facts.AnalyticsRepository"
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_latest_summary_cache.return_value = None
            mock_repo_cls.return_value = mock_repo

            result = extract_facts(db_session)

        assert result is None

    def test_extracts_facts_with_seeded_data(self, seed_analytics_data):
        db = seed_analytics_data
        result = extract_facts(db)

        assert result is not None
        assert isinstance(result, FactBundle)
        assert result.snapshot_id != ""
        assert result.current_month != ""
        assert result.total_payroll > 0
        assert result.total_claims > 0
        assert result.department_count > 0
        assert len(result.top_departments) > 0
        assert len(result.department_rankings) > 0
        assert len(result.claim_type_breakdown) > 0

    def test_fact_bundle_fields_populated(self, seed_analytics_data):
        db = seed_analytics_data
        result = extract_facts(db)

        assert result is not None
        assert result.previous_month is not None
        for d in result.top_departments:
            assert d.id != ""
            assert d.name != ""
            assert isinstance(d.total_spend, float)
            assert isinstance(d.change_pct, float)
        for c in result.claim_type_breakdown:
            assert c.type != ""
            assert isinstance(c.amount, float)
            assert isinstance(c.count, int)

    def test_claim_type_breakdown_sorted_by_amount(self, seed_analytics_data):
        db = seed_analytics_data
        result = extract_facts(db)

        assert result is not None
        amounts = [c.amount for c in result.claim_type_breakdown]
        assert amounts == sorted(amounts, reverse=True)

    def test_department_rankings_sorted_by_spend(self, seed_analytics_data):
        db = seed_analytics_data
        result = extract_facts(db)

        assert result is not None
        totals = [r.total_spend for r in result.department_rankings]
        assert totals == sorted(totals, reverse=True)
