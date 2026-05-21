import pytest

from insights.domain import (
    AnomalyFact,
    ClaimTypeFact,
    DepartmentRankingFact,
    FactBundle,
    TopDepartmentFact,
)
from insights.fallback import (
    build_fallback_findings,
    build_fallback_recommendations,
    build_fallback_summary,
)

pytestmark = pytest.mark.business_rule


def _make_facts(
    anomaly_count: int = 2,
    total_payroll: float = 1000000.0,
    total_claims: float = 50000.0,
    include_anomaly_facts: bool = False,
) -> FactBundle:
    anomalies: list[AnomalyFact] = []
    if include_anomaly_facts:
        anomalies = [
            AnomalyFact(department_name="Engineering", severity="high", description="Spike"),
            AnomalyFact(department_name="Sales", severity="medium", description="Increase"),
        ]
    return FactBundle(
        snapshot_id="snap-1",
        current_month="2026-05",
        previous_month="2026-04",
        total_payroll=total_payroll,
        total_claims=total_claims,
        department_count=4,
        anomaly_count=anomaly_count,
        anomalies=anomalies,
        top_departments=[
            TopDepartmentFact(
                id="dept-1", name="Engineering",
                total_spend=400000.0, payroll_spend=380000.0,
                claims_spend=20000.0, change_pct=15.0,
            ),
            TopDepartmentFact(
                id="dept-2", name="Sales",
                total_spend=300000.0, payroll_spend=280000.0,
                claims_spend=20000.0, change_pct=5.0,
            ),
        ],
        claim_type_breakdown=[
            ClaimTypeFact(type="Travel", amount=30000.0, count=10),
            ClaimTypeFact(type="Equipment", amount=20000.0, count=5),
        ],
        department_rankings=[
            DepartmentRankingFact(name="Engineering", total_spend=400000.0),
            DepartmentRankingFact(name="Sales", total_spend=300000.0),
            DepartmentRankingFact(name="Marketing", total_spend=200000.0),
            DepartmentRankingFact(name="Finance", total_spend=150000.0),
        ],
    )


class TestFallbackSummary:
    def test_summary_contains_month(self):
        facts = _make_facts()
        result = build_fallback_summary(facts)

        assert "2026-05" in result

    def test_summary_contains_overview(self):
        facts = _make_facts()
        result = build_fallback_summary(facts)

        assert "1,050,000.00" in result
        assert "4 departments" in result

    def test_summary_mentions_anomalies_when_present(self):
        facts = _make_facts(anomaly_count=3)
        result = build_fallback_summary(facts)

        assert "3 spending anomaly" in result

    def test_summary_mentions_no_anomalies_when_zero(self):
        facts = _make_facts(anomaly_count=0)
        result = build_fallback_summary(facts)

        assert "No spending anomalies" in result

    def test_summary_includes_top_departments(self):
        facts = _make_facts()
        result = build_fallback_summary(facts)

        assert "Engineering" in result
        assert "Sales" in result

    def test_summary_includes_claim_type_distribution(self):
        facts = _make_facts()
        result = build_fallback_summary(facts)

        assert "Travel" in result
        assert "Equipment" in result


class TestFallbackRecommendations:
    def test_includes_anomaly_review_when_anomalies_present(self):
        facts = _make_facts(anomaly_count=2)
        recs = build_fallback_recommendations(facts)

        assert any("anomalies" in r.lower() for r in recs)

    def test_includes_high_change_departments(self):
        facts = _make_facts()
        recs = build_fallback_recommendations(facts)

        assert any("Engineering" in r for r in recs)

    def test_returns_max_five(self):
        facts = _make_facts()
        recs = build_fallback_recommendations(facts)

        assert len(recs) <= 5

    def test_returns_non_empty(self):
        facts = _make_facts()
        recs = build_fallback_recommendations(facts)

        assert len(recs) > 0


class TestFallbackFindings:
    def test_includes_payroll_percentage(self):
        facts = _make_facts()
        findings = build_fallback_findings(facts)

        assert any("Payroll" in f for f in findings)

    def test_includes_top_departments(self):
        facts = _make_facts()
        findings = build_fallback_findings(facts)

        assert any("Engineering" in f for f in findings)
        assert any("Sales" in f for f in findings)

    def test_includes_largest_claim_category(self):
        facts = _make_facts()
        findings = build_fallback_findings(facts)

        assert any("Travel" in f for f in findings)

    def test_returns_max_five(self):
        facts = _make_facts()
        findings = build_fallback_findings(facts)

        assert len(findings) <= 5

    def test_anomaly_severity_counting(self):
        """lines 100-109: severity breakdown in findings."""
        facts = _make_facts(anomaly_count=2, include_anomaly_facts=True)
        findings = build_fallback_findings(facts)
        severity_text = " ".join(findings)
        assert "high-severity" in severity_text
        assert "medium-severity" in severity_text

    def test_handles_zero_anomalies(self):
        facts = _make_facts(anomaly_count=0)
        findings = build_fallback_findings(facts)

        assert not any("high-severity" in f for f in findings)
        assert not any("medium-severity" in f for f in findings)

    def test_handles_zero_total_for_percentage(self):
        facts = _make_facts(total_payroll=0.0, total_claims=0.0)
        findings = build_fallback_findings(facts)

        assert any("Payroll" in f for f in findings)
