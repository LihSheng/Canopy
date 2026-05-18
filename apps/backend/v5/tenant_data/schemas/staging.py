import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from v5.tenant_data.base import TenantDataBase

# PostgreSQL: staging.normalized_rows  |  SQLite: normalized_rows
RLS_POLICY_NAME = "tenant_isolation"


class NormalizedRowModel(TenantDataBase):
    __tablename__ = "normalized_rows"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    source_batch_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    row_index: Mapped[int] = mapped_column(Integer, nullable=False)
    normalized_data_json: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    @staticmethod
    def get_rls_policy_sql() -> str:
        table = "normalized_rows"
        return (
            f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;\n"
            f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;\n"
            f"CREATE POLICY tenant_isolation ON {table} "
            "USING (tenant_id = current_setting('app.current_tenant_id')::uuid);"
        )
