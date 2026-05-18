import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from common.clock import utcnow
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
from ontology.orchestration.service import OntologyOrchestrator
from ontology.repositories.ontology import OntologyRepository
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
def app_session(engine):
    from common.database import Base

    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
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
            amount=100.0,
            currency="MYR",
        )
        repo.save_expense_claims([claim])

        assert repo.expense_claim_count_for_snapshot("s1") == 1
        model = app_session.get(ExpenseClaimModel, "c1")
        assert model is not None
        assert model.amount == 100.0

    def test_save_payroll_with_lineage(self, app_session):
        repo = OntologyRepository(app_session)
        payroll = PayrollExpense(
            id="p1",
            snapshot_id="s1",
            source_payroll_key="P001",
            source_lineage='{"source_key":"P001"}',
            employee_id="e1",
            department_id="d1",
            amount=250.0,
            currency="MYR",
        )
        repo.save_payroll_expenses([payroll])

        assert repo.payroll_expense_count_for_snapshot("s1") == 1
        model = app_session.get(PayrollExpenseModel, "p1")
        assert model is not None
        assert model.amount == 250.0

    def test_unresolved_record_persistence(self, app_session):
        repo = OntologyRepository(app_session)
        unresolved = UnresolvedRecord(
            entity_type="employees",
            source_key="E999",
            reason="Missing department",
            source_data={"snapshot_id": "s1"},
        )
        repo.save_unresolved_issues("s1", [unresolved])

        assert repo.unresolved_issue_count_for_snapshot("s1") == 1

        model = app_session.query(UnresolvedMappingIssueModel).filter(
            UnresolvedMappingIssueModel.snapshot_id == "s1"
        ).first()
        assert model is not None
        assert model.reason == "Missing department"
