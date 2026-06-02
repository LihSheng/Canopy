"""add tenant_id columns to projects connections datasets runs

Revision ID: b3d4e5f6a7c8
Revises: a2c3d4e5f6a7
Create Date: 2026-06-02 18:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b3d4e5f6a7c8"
down_revision: str | Sequence[str] | None = "a2c3d4e5f6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("projects", sa.Column("tenant_id", sa.String(36), nullable=True))
    op.create_index("ix_projects_tenant_id", "projects", ["tenant_id"])

    op.add_column("connections", sa.Column("tenant_id", sa.String(36), nullable=True))
    op.create_index("ix_connections_tenant_id", "connections", ["tenant_id"])

    op.add_column("datasets", sa.Column("tenant_id", sa.String(36), nullable=True))
    op.create_index("ix_datasets_tenant_id", "datasets", ["tenant_id"])

    op.add_column("runs", sa.Column("tenant_id", sa.String(36), nullable=True))
    op.create_index("ix_runs_tenant_id", "runs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_runs_tenant_id", table_name="runs")
    op.drop_column("runs", "tenant_id")

    op.drop_index("ix_datasets_tenant_id", table_name="datasets")
    op.drop_column("datasets", "tenant_id")

    op.drop_index("ix_connections_tenant_id", table_name="connections")
    op.drop_column("connections", "tenant_id")

    op.drop_index("ix_projects_tenant_id", table_name="projects")
    op.drop_column("projects", "tenant_id")
