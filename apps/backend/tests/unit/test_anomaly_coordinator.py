import pytest

pytestmark = pytest.mark.business_rule

from unittest.mock import MagicMock, patch

from analytics.domain import MonthlyDepartmentSpend
from anomalies.service import detect_anomalies


def _make_spend(
    dept_id: str, month: str, payroll: float, claims: float, claim_count: int = 0
) -> MonthlyDepartmentSpend:
    return MonthlyDepartmentSpend(
        id=f"{dept_id}-{month}",
        snapshot_id="snap-1",
        department_id=dept_id,
        month=month,
        payroll_total=payroll,
        claims_total=claims,
        total=payroll + claims,
        claim_count=claim_count,
    )


class TestAnomalyDetector:
    def test_detects_multiple_rule_outputs(self, db_session):
        snapshot_id = "snap-test"
        prev = [
            _make_spend("dept-a", "2026-04", 50000, 5000),
            _make_spend("dept-b", "2026-04", 30000, 30000),
        ]
        cur = [
            _make_spend("dept-a", "2026-05", 80000, 6000),
            _make_spend("dept-b", "2026-05", 30000, 60000),
        ]

        with patch(
            "anomalies.service.get_monthly_spends_for_month",
            side_effect=[cur, prev],
        ):
            results = detect_anomalies(db_session, snapshot_id, "2026-05", "2026-04")

        assert len(results) > 0
        dept_a_found = any(r.target_entity_id == "dept-a" for r in results)
        dept_b_found = any(r.target_entity_id == "dept-b" for r in results)
        assert dept_a_found
        assert dept_b_found

    def test_empty_spends_produces_no_anomalies(self, db_session):
        with patch(
            "anomalies.service.get_monthly_spends_for_month",
            return_value=[],
        ):
            results = detect_anomalies(db_session, "snap-1", "2026-05", "2026-04")

        assert len(results) == 0
