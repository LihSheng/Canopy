from collections.abc import Callable
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.orm import Session

if TYPE_CHECKING:
    from sqlalchemy.orm import DeclarativeBase


def is_rls_supported(db_session: Session) -> bool:
    dialect_name = db_session.bind.dialect.name if db_session.bind else ""
    return dialect_name == "postgresql"


def _rls_ddl_for_table(table_name: str) -> tuple[str, str]:
    enable = (
        f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;\nALTER TABLE {table_name} FORCE ROW LEVEL SECURITY;\n"
    )
    policy = (
        f"CREATE POLICY tenant_isolation ON {table_name} USING (tenant_id = current_setting('app.current_tenant_id'));"
    )
    return enable, policy


def generate_rls_policies(base_class: "type[DeclarativeBase] | None", table_names: list[str]) -> str:
    lines: list[str] = []
    for table_name in table_names:
        enable, policy = _rls_ddl_for_table(table_name)
        lines.append(enable.rstrip())
        lines.append(policy)
        lines.append("")
    return "\n".join(lines).rstrip("\n")


def generate_rls_rollback(base_class: "type[DeclarativeBase] | None", table_names: list[str]) -> str:
    lines: list[str] = []
    for table_name in reversed(table_names):
        lines.append(f"DROP POLICY IF EXISTS tenant_isolation ON {table_name};")
        lines.append(f"ALTER TABLE {table_name} NO FORCE ROW LEVEL SECURITY;")
        lines.append(f"ALTER TABLE {table_name} DISABLE ROW LEVEL SECURITY;")
        lines.append("")
    return "\n".join(lines).rstrip("\n")


def apply_rls(db_session: Session, table_names: list[str]) -> None:
    if not is_rls_supported(db_session):
        return
    for table_name in table_names:
        enable, policy = _rls_ddl_for_table(table_name)
        db_session.execute(text(enable))
        db_session.execute(text(policy))


def apply_rls_with_policy_sql(db_session: Session, policy_sql_provider: Callable[[], str]) -> None:
    if not is_rls_supported(db_session):
        return
    db_session.execute(text(policy_sql_provider()))


ALL_TENANT_DATA_TABLES = [
    "upload_batches",
    "raw_artifacts",
    "normalized_rows",
    "cleaned_records",
    "derived_read_models",
    "lineage_nodes",
    "lineage_edges",
    "publish_states",
    "storage_objects",
    "job_runs",
]
