import uuid

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from common.database import Base


class MonthlyDepartmentSpendModel(Base):
    __tablename__ = "analytics_monthly_department_spend"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    department_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    month: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    payroll_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    claims_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    claim_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class MonthlyEmployeeSpendModel(Base):
    __tablename__ = "analytics_monthly_employee_spend"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    employee_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    department_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    month: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    payroll_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    claims_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)


class MonthlyClaimTypeSpendModel(Base):
    __tablename__ = "analytics_monthly_claim_type_spend"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    department_id: Mapped[str | None] = mapped_column(String(36), nullable=True, index=True)
    claim_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    month: Mapped[str] = mapped_column(String(16), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    claim_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class DashboardSummaryCacheModel(Base):
    __tablename__ = "analytics_dashboard_summary_cache"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    snapshot_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    total_payroll: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    total_claims: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    department_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    anomaly_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[str] = mapped_column(String(32), nullable=False, default="")
