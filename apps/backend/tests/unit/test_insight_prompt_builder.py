import pytest

pytestmark = pytest.mark.business_rule

from insights.domain import (
    AnomalyFact,
    ClaimTypeFact,
    DepartmentRankingFact,
    FactBundle,
    TopDepartmentFact,
)
from insights.prompt_builder import build_prompt


def _make_fact_bundle() -> FactBundle:
    return FactBundle(
        snapshot_id="snap-1",
        current_month="2026-05",
        previous_month="2026-04",
        total_payroll=1490500.0,
        total_claims=13770.0,
        department_count=6,
        anomaly_count=2,
        top_departments=[
            TopDepartmentFact(
                id="dept-1", name="Engineering",
                total_spend=446300.0, payroll_spend=440000.0,
                claims_spend=6300.0, change_pct=2.6,
            ),
            TopDepartmentFact(
                id="dept-2", name="Sales",
                total_spend=328550.0, payroll_spend=325000.0,
                claims_spend=3550.0, change_pct=0.9,
            ),
        ],
        anomalies=[
            AnomalyFact(
                department_name="Engineering",
                severity="medium", description="Claims +15% MoM.",
                change_pct=15.0,
            ),
            AnomalyFact(
                department_name="Sales",
                severity="low", description="Total spend +0.9% MoM.",
                change_pct=0.9,
            ),
        ],
        claim_type_breakdown=[
            ClaimTypeFact(type="Travel", amount=8000.0, count=3),
            ClaimTypeFact(type="Equipment", amount=2500.0, count=1),
        ],
        department_rankings=[
            DepartmentRankingFact(name="Engineering", total_spend=446300.0),
            DepartmentRankingFact(name="Sales", total_spend=328550.0),
        ],
    )


class TestPromptBuilder:
    def test_build_prompt_contains_summary_metrics(self):
        facts = _make_fact_bundle()
        prompt = build_prompt(facts)

        assert "2026-05" in prompt
        assert "2026-04" in prompt
        assert "1,490,500.00" in prompt
        assert "13,770.00" in prompt

    def test_build_prompt_contains_top_departments(self):
        facts = _make_fact_bundle()
        prompt = build_prompt(facts)

        assert "Engineering" in prompt
        assert "Sales" in prompt

    def test_build_prompt_contains_anomalies(self):
        facts = _make_fact_bundle()
        prompt = build_prompt(facts)

        assert "[MEDIUM]" in prompt
        assert "Claims +15% MoM" in prompt

    def test_build_prompt_contains_claim_types(self):
        facts = _make_fact_bundle()
        prompt = build_prompt(facts)

        assert "Travel" in prompt
        assert "Equipment" in prompt

    def test_build_prompt_contains_department_rankings(self):
        facts = _make_fact_bundle()
        prompt = build_prompt(facts)

        assert "1. Engineering" in prompt
        assert "2. Sales" in prompt

    def test_build_prompt_has_expected_json_output_format(self):
        facts = _make_fact_bundle()
        prompt = build_prompt(facts)

        assert '"summary"' in prompt
        assert '"recommendations"' in prompt
        assert '"key_findings"' in prompt

    def test_build_prompt_with_empty_lists_shows_none(self):
        facts = FactBundle(
            snapshot_id="snap-1",
            current_month="2026-05",
            previous_month=None,
        )
        prompt = build_prompt(facts)

        assert "None" in prompt

    def test_build_prompt_with_none_previous_month(self):
        facts = _make_fact_bundle()
        facts.previous_month = None
        prompt = build_prompt(facts)

        assert "N/A" in prompt
