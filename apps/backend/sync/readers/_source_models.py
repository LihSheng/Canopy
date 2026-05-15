from sqlalchemy import Float, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class SourceBase(DeclarativeBase):
    """Base for source-database models. Never mixed with application Base."""


class SourceDepartmentRow(SourceBase):
    __tablename__ = "departments"

    source_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")


class SourceEmployeeRow(SourceBase):
    __tablename__ = "employees"

    source_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_key: Mapped[str] = mapped_column(String(128), nullable=False)
    cost_center_key: Mapped[str | None] = mapped_column(String(128), nullable=True)


class SourceClaimRow(SourceBase):
    __tablename__ = "claims"

    source_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    employee_key: Mapped[str] = mapped_column(String(128), nullable=False)
    department_key: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    claim_type: Mapped[str] = mapped_column(String(64), nullable=False)
    submitted_at: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)


class SourcePayrollRow(SourceBase):
    __tablename__ = "payroll"

    source_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    employee_key: Mapped[str] = mapped_column(String(128), nullable=False)
    department_key: Mapped[str] = mapped_column(String(128), nullable=False)
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(8), nullable=False)
    period_start: Mapped[str] = mapped_column(String(16), nullable=False)
    period_end: Mapped[str] = mapped_column(String(16), nullable=False)


class SourceCostCenterRow(SourceBase):
    __tablename__ = "cost_centers"

    source_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_key: Mapped[str | None] = mapped_column(String(128), nullable=True)


class SourceBudgetCodeRow(SourceBase):
    __tablename__ = "budget_codes"

    source_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_key: Mapped[str | None] = mapped_column(String(128), nullable=True)
