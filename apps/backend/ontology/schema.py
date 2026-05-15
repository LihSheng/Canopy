import uuid
from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class DepartmentModel(Base):
    __tablename__ = "departments"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_department_key: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    source_lineage: Mapped[str] = mapped_column(Text, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_department_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class EmployeeModel(Base):
    __tablename__ = "employees"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_employee_key: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    source_lineage: Mapped[str] = mapped_column(Text, nullable=False)
    department_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    cost_center_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    employee_code: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    employment_status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active"
    )


class CostCenterModel(Base):
    __tablename__ = "cost_centers"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_cost_center_key: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    source_lineage: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)


class BudgetCodeModel(Base):
    __tablename__ = "budget_codes"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_budget_code_key: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    source_lineage: Mapped[str] = mapped_column(Text, nullable=False)
    code: Mapped[str] = mapped_column(String(64), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False, default="")


class ExpenseClaimModel(Base):
    __tablename__ = "expense_claims"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_claim_key: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    source_lineage: Mapped[str] = mapped_column(Text, nullable=False)
    employee_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    department_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    cost_center_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    budget_code_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    claim_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    claim_date: Mapped[str] = mapped_column(String(32), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="MYR")
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class PayrollExpenseModel(Base):
    __tablename__ = "payroll_expenses"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_payroll_key: Mapped[str] = mapped_column(
        String(128), nullable=False, index=True
    )
    source_lineage: Mapped[str] = mapped_column(Text, nullable=False)
    employee_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    department_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True
    )
    cost_center_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    budget_code_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    payroll_month: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False, default="MYR")
    pay_component: Mapped[str] = mapped_column(
        String(64), nullable=False, default=""
    )
    is_resolved: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class UnresolvedMappingIssueModel(Base):
    __tablename__ = "unresolved_mapping_issues"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_key: Mapped[str] = mapped_column(String(128), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    source_data: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        nullable=False,
    )
