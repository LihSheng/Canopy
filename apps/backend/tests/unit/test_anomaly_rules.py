import pytest

pytestmark = pytest.mark.business_rule

from analytics.domain import MonthlyDepartmentSpend
from anomalies.rules.department_claim_spike import department_claim_spike_rule
from anomalies.rules.department_total_spike import department_total_spike_rule

SNAPSHOT_ID = "test-snapshot-001"


def _make_spend(
    dept_id: str, month: str, payroll: float, claims: float, claim_count: int = 0
) -> MonthlyDepartmentSpend:
    return MonthlyDepartmentSpend(
        id=f"{dept_id}-{month}",
        snapshot_id=SNAPSHOT_ID,
        department_id=dept_id,
        month=month,
        payroll_total=payroll,
        claims_total=claims,
        total=payroll + claims,
        claim_count=claim_count,
    )


class TestDepartmentTotalSpikeRule:
    def test_detects_high_increase(self):
        prev = [_make_spend("dept-1", "2026-04", 50000, 10000)]
        cur = [_make_spend("dept-1", "2026-05", 65000, 15000)]

        results = department_total_spike_rule(SNAPSHOT_ID, cur, prev)

        assert len(results) == 1
        r = results[0]
        assert r.anomaly_type == "department_total_spike"
        assert r.target_entity_id == "dept-1"
        assert r.month_key == "2026-05"
        assert r.baseline_value == 60000
        assert r.observed_value == 80000
        assert r.delta_value == 20000
        assert r.delta_percent == 33.33
        assert r.severity in ("high", "medium")
        assert len(r.driver_details) > 0

    def test_detects_decrease(self):
        prev = [_make_spend("dept-1", "2026-04", 100000, 20000)]
        cur = [_make_spend("dept-1", "2026-05", 70000, 15000)]

        results = department_total_spike_rule(SNAPSHOT_ID, cur, prev)

        assert len(results) == 1
        r = results[0]
        assert r.delta_value < 0
        assert r.delta_percent < 0
        assert r.severity != "low"

    def test_ignores_below_threshold(self):
        prev = [_make_spend("dept-1", "2026-04", 100000, 20000)]
        cur = [_make_spend("dept-1", "2026-05", 101000, 20000)]

        results = department_total_spike_rule(SNAPSHOT_ID, cur, prev)

        assert len(results) == 0

    def test_skips_new_department_zero_previous(self):
        prev: list[MonthlyDepartmentSpend] = []
        cur = [_make_spend("dept-new", "2026-05", 50000, 10000)]

        results = department_total_spike_rule(SNAPSHOT_ID, cur, prev)

        assert len(results) == 0

    def test_multiple_departments(self):
        prev = [
            _make_spend("dept-1", "2026-04", 100000, 50000),
            _make_spend("dept-2", "2026-04", 80000, 20000),
            _make_spend("dept-3", "2026-04", 50000, 10000),
        ]
        cur = [
            _make_spend("dept-1", "2026-05", 120000, 55000),
            _make_spend("dept-2", "2026-05", 80000, 21000),
            _make_spend("dept-3", "2026-05", 200000, 50000),
        ]

        results = department_total_spike_rule(SNAPSHOT_ID, cur, prev)

        dept_ids = {r.target_entity_id for r in results}
        assert "dept-1" in dept_ids
        assert "dept-3" in dept_ids
        assert "dept-2" not in dept_ids

    def test_custom_threshold(self):
        prev = [_make_spend("dept-1", "2026-04", 100000, 20000)]
        cur = [_make_spend("dept-1", "2026-05", 110000, 20000)]

        results_default = department_total_spike_rule(SNAPSHOT_ID, cur, prev)
        assert len(results_default) == 1

        results_strict = department_total_spike_rule(SNAPSHOT_ID, cur, prev, threshold_pct=15.0)
        assert len(results_strict) == 0

    def test_output_has_all_fields(self):
        prev = [_make_spend("dept-1", "2026-04", 100000, 20000)]
        cur = [_make_spend("dept-1", "2026-05", 200000, 30000)]

        results = department_total_spike_rule(SNAPSHOT_ID, cur, prev)

        r = results[0]
        assert r.id
        assert r.snapshot_id == SNAPSHOT_ID
        assert r.description
        assert r.delta_value is not None
        assert r.delta_percent is not None


class TestDepartmentClaimSpikeRule:
    def test_detects_claim_increase(self):
        prev = [_make_spend("dept-1", "2026-04", 50000, 10000, claim_count=5)]
        cur = [_make_spend("dept-1", "2026-05", 50000, 22000, claim_count=10)]

        results = department_claim_spike_rule(SNAPSHOT_ID, cur, prev)

        assert len(results) == 1
        r = results[0]
        assert r.anomaly_type == "department_claim_spike"
        assert r.baseline_value == 10000
        assert r.observed_value == 22000
        assert r.delta_percent == 120.0

    def test_ignores_small_claim_change(self):
        prev = [_make_spend("dept-1", "2026-04", 50000, 10000)]
        cur = [_make_spend("dept-1", "2026-05", 50000, 10500)]

        results = department_claim_spike_rule(SNAPSHOT_ID, cur, prev)

        assert len(results) == 0

    def test_detects_claim_drop(self):
        prev = [_make_spend("dept-1", "2026-04", 50000, 20000)]
        cur = [_make_spend("dept-1", "2026-05", 50000, 10000)]

        results = department_claim_spike_rule(SNAPSHOT_ID, cur, prev)

        assert len(results) == 1
        r = results[0]
        assert r.delta_value < 0
        assert r.delta_percent < 0

    def test_new_claims_from_zero(self):
        prev = [_make_spend("dept-1", "2026-04", 50000, 0)]
        cur = [_make_spend("dept-1", "2026-05", 50000, 5000, claim_count=3)]

        results = department_claim_spike_rule(SNAPSHOT_ID, cur, prev)

        assert len(results) == 1
        r = results[0]
        assert r.delta_percent == 100.0

    def test_both_zero_claims(self):
        prev = [_make_spend("dept-1", "2026-04", 50000, 0)]
        cur = [_make_spend("dept-1", "2026-05", 50000, 0)]

        results = department_claim_spike_rule(SNAPSHOT_ID, cur, prev)

        assert len(results) == 0

    def test_claim_driver_details(self):
        prev = [_make_spend("dept-1", "2026-04", 50000, 10000, claim_count=3)]
        cur = [_make_spend("dept-1", "2026-05", 50000, 25000, claim_count=8)]

        results = department_claim_spike_rule(SNAPSHOT_ID, cur, prev)

        r = results[0]
        assert len(r.driver_details) > 0
        assert any("claims" in d.lower() for d in r.driver_details)
