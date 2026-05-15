import uuid

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.pool import StaticPool

from common.clock import utcnow
from common.database import Base, reset_engine, set_engine
from ontology.domain import (
    BudgetCode,
    CostCenter,
    Department,
    Employee,
    ExpenseClaim,
    MappingContext,
    PayrollExpense,
    UnresolvedRecord,
)
from ontology.mappers import (
    BudgetCodeMapper,
    CostCenterMapper,
    DepartmentMapper,
    EmployeeMapper,
)
from ontology.repositories.ontology import OntologyRepository
from ontology.orchestration.service import OntologyOrchestrator
from ontology.schema import (
    DepartmentModel,
    EmployeeModel,
    ExpenseClaimModel,
    PayrollExpenseModel,
    UnresolvedMappingIssueModel,
)
from sync.domain import (
    SourceBudgetCode,
    SourceClaim,
    SourceCostCenter,
    SourceDepartment,
    SourceEmployee,
    SourcePayroll,
)


@pytest.fixture
def app_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    set_engine(engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    reset_engine()


@pytest.fixture
def app_session(app_engine):
    from sqlalchemy.orm import sessionmaker

    factory = sessionmaker(autocommit=False, autoflush=False, bind=app_engine)
    session = factory()
    try:
        yield session
    finally:
        session.close()


class TestOntologyRepository:
    def test_save_and_count_departments(self, app_session):
        repo = OntologyRepository(app_session)
        dept = Department(
            id="d1",
            snapshot_id="s1",
            source_department_key="D001",
            source_lineage='{"source_key":"D001"}',
            name="Engineering",
            status="active",
        )
        repo.save_departments([dept])

        assert repo.department_count_for_snapshot("s1") == 1
        assert repo.department_count_for_snapshot("nonexistent") == 0

        model = app_session.get(DepartmentModel, "d1")
        assert model is not None
        assert model.name == "Engineering"
        assert model.source_department_key == "D001"
        assert model.source_lineage is not None

    def test_save_and_count_employees(self, app_session):
        repo = OntologyRepository(app_session)
        emp = Employee(
            id="e1",
            snapshot_id="s1",
            source_employee_key="E001",
            source_lineage="{}",
            department_id="d1",
            full_name="Alice",
            employee_code="E001",
        )
        repo.save_employees([emp])

        assert repo.employee_count_for_snapshot("s1") == 1

        model = app_session.get(EmployeeModel, "e1")
        assert model is not None
        assert model.full_name == "Alice"

    def test_save_expense_claims_with_lineage(self, app_session):
        repo = OntologyRepository(app_session)
        claim = ExpenseClaim(
            id="c1",
            snapshot_id="s1",
            source_claim_key="C001",
            source_lineage='{"source_key":"C001"}',
            employee_id="e1",
            department_id="d1",
            claim_type="travel",
            claim_date="2025-01-15",
            amount=150.0,
            currency="MYR",
            is_resolved=True,
        )
        repo.save_expense_claims([claim])

        assert repo.expense_claim_count_for_snapshot("s1") == 1

        model = app_session.get(ExpenseClaimModel, "c1")
        assert model is not None
        assert model.source_lineage is not None
        assert model.amount == 150.0

    def test_save_unresolved_claim_still_persisted(self, app_session):
        repo = OntologyRepository(app_session)
        claim = ExpenseClaim(
            id="c2",
            snapshot_id="s1",
            source_claim_key="C002",
            source_lineage="{}",
            employee_id="e1",
            department_id=None,
            claim_type="travel",
            claim_date="2025-01-15",
            amount=200.0,
            is_resolved=False,
        )
        repo.save_expense_claims([claim])

        assert repo.expense_claim_count_for_snapshot("s1") == 1

        model = app_session.get(ExpenseClaimModel, "c2")
        assert model is not None
        assert model.is_resolved is False
        assert model.department_id is None

    def test_save_payroll_expenses(self, app_session):
        repo = OntologyRepository(app_session)
        pe = PayrollExpense(
            id="p1",
            snapshot_id="s1",
            source_payroll_key="P001",
            source_lineage="{}",
            employee_id="e1",
            department_id="d1",
            payroll_month="2025-01",
            amount=5000.0,
            currency="MYR",
            pay_component="base_salary",
            is_resolved=True,
        )
        repo.save_payroll_expenses([pe])

        assert repo.payroll_expense_count_for_snapshot("s1") == 1

        model = app_session.get(PayrollExpenseModel, "p1")
        assert model is not None
        assert model.payroll_month == "2025-01"

    def test_save_unresolved_issues(self, app_session):
        repo = OntologyRepository(app_session)
        issues = [
            UnresolvedRecord(
                source_key="E999",
                entity_type="employees",
                reason="department D999 not found",
                source_data={"source_key": "E999", "full_name": "Ghost"},
            )
        ]
        repo.save_unresolved_issues("s1", issues)

        assert repo.unresolved_issue_count_for_snapshot("s1") == 1

        stmt = select(UnresolvedMappingIssueModel).where(
            UnresolvedMappingIssueModel.snapshot_id == "s1"
        )
        row = app_session.execute(stmt).scalars().first()
        assert row is not None
        assert row.source_key == "E999"
        assert "D999" in row.reason

    def test_save_multiple_entities(self, app_session):
        repo = OntologyRepository(app_session)
        departments = [
            Department(id="d1", snapshot_id="s1", source_department_key="D001",
                        source_lineage="{}", name="Eng"),
            Department(id="d2", snapshot_id="s1", source_department_key="D002",
                        source_lineage="{}", name="Mktg"),
        ]
        repo.save_departments(departments)
        assert repo.department_count_for_snapshot("s1") == 2


class TestOntologyOrchestrator:
    def test_full_mapping_pipeline(self, app_session):
        orchestrator = OntologyOrchestrator(app_session)

        source_deps = [
            SourceDepartment(source_key="D001", name="Engineering"),
            SourceDepartment(source_key="D002", name="Marketing"),
        ]
        source_emps = [
            SourceEmployee(source_key="E001", full_name="Alice Tan",
                           department_key="D001"),
            SourceEmployee(source_key="E002", full_name="Bob Lim",
                           department_key="D002"),
        ]
        source_cc = [
            SourceCostCenter(source_key="CC001", name="R&D"),
        ]
        source_bc = [
            SourceBudgetCode(source_key="B001", name="Opex-IT"),
        ]
        source_claims = [
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
        source_payroll = [
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

        results = orchestrator.map_all(
            snapshot_id="snap-001",
            departments=source_deps,
            employees=source_emps,
            cost_centers=source_cc,
            budget_codes=source_bc,
            claims=source_claims,
            payroll=source_payroll,
        )

        assert len(results) == 6
        assert results[0].entity_type == "departments"
        assert results[1].entity_type == "cost_centers"
        assert results[2].entity_type == "budget_codes"
        assert results[3].entity_type == "employees"
        assert results[4].entity_type == "expense_claims"
        assert results[5].entity_type == "payroll_expenses"

        repo = OntologyRepository(app_session)
        assert repo.department_count_for_snapshot("snap-001") == 2
        assert repo.employee_count_for_snapshot("snap-001") == 2
        assert repo.expense_claim_count_for_snapshot("snap-001") == 1
        assert repo.payroll_expense_count_for_snapshot("snap-001") == 1

    def test_unresolved_employee_is_recorded(self, app_session):
        orchestrator = OntologyOrchestrator(app_session)

        source_deps = [
            SourceDepartment(source_key="D001", name="Engineering"),
        ]
        source_emps = [
            SourceEmployee(source_key="E001", full_name="Alice",
                           department_key="D999"),
        ]

        results = orchestrator.map_all(
            snapshot_id="snap-002",
            departments=source_deps,
            employees=source_emps,
            cost_centers=[],
            budget_codes=[],
            claims=[],
            payroll=[],
        )

        emp_result = [r for r in results if r.entity_type == "employees"][0]
        assert len(emp_result.mapped) == 0
        assert len(emp_result.unresolved) == 1

        repo = OntologyRepository(app_session)
        assert repo.employee_count_for_snapshot("snap-002") == 0
        assert repo.unresolved_issue_count_for_snapshot("snap-002") == 1

    def test_unresolved_claim_department_is_still_persisted(self, app_session):
        orchestrator = OntologyOrchestrator(app_session)

        source_deps = [
            SourceDepartment(source_key="D001", name="Engineering"),
        ]
        source_emps = [
            SourceEmployee(source_key="E001", full_name="Alice",
                           department_key="D001"),
        ]
        source_claims = [
            SourceClaim(
                source_key="C001",
                employee_key="E001",
                department_key="D999",
                amount=200.0,
                currency="MYR",
                claim_type="travel",
                submitted_at="2025-01-15T10:00:00",
                status="approved",
            )
        ]

        results = orchestrator.map_all(
            snapshot_id="snap-003",
            departments=source_deps,
            employees=source_emps,
            cost_centers=[],
            budget_codes=[],
            claims=source_claims,
            payroll=[],
        )

        emp_result = [r for r in results if r.entity_type == "employees"][0]
        assert len(emp_result.mapped) == 1

        claim_result = [r for r in results if r.entity_type == "expense_claims"][0]
        assert len(claim_result.mapped) == 1
        assert claim_result.mapped[0].is_resolved is True
        assert claim_result.mapped[0].department_id == emp_result.mapped[0].department_id
        assert len(claim_result.unresolved) == 0

        repo = OntologyRepository(app_session)
        assert repo.expense_claim_count_for_snapshot("snap-003") == 1
        assert repo.department_count_for_snapshot("snap-003") == 1
