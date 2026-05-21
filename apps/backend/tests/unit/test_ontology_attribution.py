import pytest

import json
from dataclasses import asdict

from ontology.domain import (
    CostCenter,
    Department,
    Employee,
    MappingContext,
)
from ontology.mappers.attribution import AttributionResolver
from ontology.mappers.claims import ClaimMapper
from ontology.mappers.payroll import PayrollMapper
from sync.domain import SourceClaim, SourcePayroll

pytestmark = pytest.mark.business_rule


def _make_dept(key, id_, name):
    return Department(
        id=id_, snapshot_id="s1", source_department_key=key,
        source_lineage="{}", name=name,
    )


def _make_emp(key, id_, dept_id):
    return Employee(
        id=id_, snapshot_id="s1", source_employee_key=key,
        source_lineage="{}", department_id=dept_id, full_name="Alice",
    )


class TestAttributionResolver:
    def test_direct_department_wins(self):
        resolver = AttributionResolver()
        dept = _make_dept("D001", "d1", "Engineering")
        context = MappingContext(
            snapshot_id="s1", departments={"D001": dept}
        )
        result = resolver.resolve_department(
            context,
            direct_department_key="D001",
            employee_source_key=None,
            cost_center_source_key=None,
        )
        assert result == "d1"

    def test_fallback_to_employee_department(self):
        resolver = AttributionResolver()
        dept = _make_dept("D001", "d1", "Engineering")
        emp = _make_emp("E001", "e1", "d1")
        context = MappingContext(
            snapshot_id="s1",
            departments={"D001": dept},
            employees={"E001": emp},
        )
        result = resolver.resolve_department(
            context,
            direct_department_key=None,
            employee_source_key="E001",
            cost_center_source_key=None,
        )
        assert result == "d1"

    def test_missing_everywhere_returns_none(self):
        resolver = AttributionResolver()
        context = MappingContext(snapshot_id="s1")
        result = resolver.resolve_department(
            context,
            direct_department_key=None,
            employee_source_key=None,
            cost_center_source_key=None,
        )
        assert result is None

    def test_unknown_direct_key_returns_none(self):
        resolver = AttributionResolver()
        context = MappingContext(snapshot_id="s1")
        result = resolver.resolve_department(
            context,
            direct_department_key="D999",
            employee_source_key=None,
            cost_center_source_key=None,
        )
        assert result is None

    def test_unknown_employee_key_returns_none(self):
        resolver = AttributionResolver()
        context = MappingContext(snapshot_id="s1")
        result = resolver.resolve_department(
            context,
            direct_department_key=None,
            employee_source_key="E999",
            cost_center_source_key=None,
        )
        assert result is None

    def test_resolve_cost_center_from_employee(self):
        resolver = AttributionResolver()
        dept = _make_dept("D001", "d1", "Engineering")
        emp = Employee(
            id="e1", snapshot_id="s1", source_employee_key="E001",
            source_lineage="{}", department_id="d1",
            cost_center_id="cc1",
        )
        context = MappingContext(
            snapshot_id="s1",
            departments={"D001": dept},
            employees={"E001": emp},
        )
        result = resolver.resolve_cost_center(context, employee_source_key="E001")
        assert result == "cc1"


class TestClaimMapperAttribution:
    def test_resolved_claim_with_direct_department(self):
        dept = _make_dept("D001", "d1", "Engineering")
        emp = _make_emp("E001", "e1", "d1")
        context = MappingContext(
            snapshot_id="snap-001",
            departments={"D001": dept},
            employees={"E001": emp},
        )
        source = [
            SourceClaim(
                source_key="C001",
                employee_key="E001",
                department_key="D001",
                amount=150.0,
                currency="MYR",
                claim_type="travel",
                submitted_at="2025-01-15T10:00:00",
                status="approved",
            )
        ]

        mapper = ClaimMapper()
        result = mapper.map(source, context)

        assert len(result.mapped) == 1
        claim = result.mapped[0]
        assert claim.is_resolved is True
        assert claim.department_id == "d1"
        assert claim.employee_id == "e1"
        assert claim.amount == 150.0
        assert claim.claim_type == "travel"
        assert claim.source_claim_key == "C001"

    def test_unknown_employee_is_unresolved(self):
        context = MappingContext(snapshot_id="snap-001")
        source = [
            SourceClaim(
                source_key="C001",
                employee_key="E999",
                department_key="D001",
                amount=150.0,
                currency="MYR",
                claim_type="travel",
                submitted_at="2025-01-15T10:00:00",
                status="approved",
            )
        ]

        mapper = ClaimMapper()
        result = mapper.map(source, context)

        assert len(result.mapped) == 0
        assert len(result.unresolved) == 1
        assert result.unresolved[0].source_key == "C001"
        assert "E999" in result.unresolved[0].reason

    def test_unresolved_department_sets_is_resolved_false(self):
        emp = _make_emp("E001", "e1", "")
        context = MappingContext(
            snapshot_id="snap-001", employees={"E001": emp}
        )
        source = [
            SourceClaim(
                source_key="C001",
                employee_key="E001",
                department_key="D999",
                amount=150.0,
                currency="MYR",
                claim_type="travel",
                submitted_at="2025-01-15T10:00:00",
                status="approved",
            )
        ]

        mapper = ClaimMapper()
        result = mapper.map(source, context)

        assert len(result.mapped) == 1
        claim = result.mapped[0]
        assert claim.is_resolved is False
        assert claim.department_id is None
        assert len(result.unresolved) == 1


class TestPayrollMapperAttribution:
    def test_resolved_payroll_with_direct_department(self):
        dept = _make_dept("D001", "d1", "Engineering")
        emp = _make_emp("E001", "e1", "d1")
        context = MappingContext(
            snapshot_id="snap-001",
            departments={"D001": dept},
            employees={"E001": emp},
        )
        source = [
            SourcePayroll(
                source_key="P001",
                employee_key="E001",
                department_key="D001",
                amount=5000.0,
                currency="MYR",
                period_start="2025-01",
                period_end="2025-01",
            )
        ]

        mapper = PayrollMapper()
        result = mapper.map(source, context)

        assert len(result.mapped) == 1
        pe = result.mapped[0]
        assert pe.is_resolved is True
        assert pe.department_id == "d1"
        assert pe.employee_id == "e1"
        assert pe.amount == 5000.0
        assert pe.payroll_month == "2025-01"
        assert pe.pay_component == "base_salary"

    def test_unknown_employee_is_unresolved(self):
        context = MappingContext(snapshot_id="snap-001")
        source = [
            SourcePayroll(
                source_key="P001",
                employee_key="E999",
                department_key="D001",
                amount=5000.0,
                currency="MYR",
                period_start="2025-01",
                period_end="2025-01",
            )
        ]

        mapper = PayrollMapper()
        result = mapper.map(source, context)

        assert len(result.mapped) == 0
        assert len(result.unresolved) == 1
        assert result.unresolved[0].source_key == "P001"

    def test_unresolved_department_sets_is_resolved_false(self):
        emp = _make_emp("E001", "e1", "")
        context = MappingContext(
            snapshot_id="snap-001", employees={"E001": emp}
        )
        source = [
            SourcePayroll(
                source_key="P001",
                employee_key="E001",
                department_key="D999",
                amount=5000.0,
                currency="MYR",
                period_start="2025-01",
                period_end="2025-01",
            )
        ]

        mapper = PayrollMapper()
        result = mapper.map(source, context)

        assert len(result.mapped) == 1
        pe = result.mapped[0]
        assert pe.is_resolved is False
        assert pe.department_id is None
        assert len(result.unresolved) == 1

    def test_payroll_month_handles_short_period_start(self):
        dept = _make_dept("D001", "d1", "Engineering")
        emp = _make_emp("E001", "e1", "d1")
        context = MappingContext(
            snapshot_id="snap-001",
            departments={"D001": dept},
            employees={"E001": emp},
        )
        source = [
            SourcePayroll(
                source_key="P001",
                employee_key="E001",
                department_key="D001",
                amount=5000.0,
                currency="MYR",
                period_start="2025-01-15",
                period_end="2025-01-31",
            )
        ]

        mapper = PayrollMapper()
        result = mapper.map(source, context)

        assert result.mapped[0].payroll_month == "2025-01"

    def test_payroll_month_handles_short_string(self):
        dept = _make_dept("D001", "d1", "Engineering")
        emp = _make_emp("E001", "e1", "d1")
        context = MappingContext(
            snapshot_id="snap-001",
            departments={"D001": dept},
            employees={"E001": emp},
        )
        source = [
            SourcePayroll(
                source_key="P001",
                employee_key="E001",
                department_key="D001",
                amount=5000.0,
                currency="MYR",
                period_start="Q1",
                period_end="Q1",
            )
        ]

        mapper = PayrollMapper()
        result = mapper.map(source, context)

        assert result.mapped[0].payroll_month == "Q1"
