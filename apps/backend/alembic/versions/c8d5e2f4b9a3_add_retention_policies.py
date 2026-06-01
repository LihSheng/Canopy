"""add retention_policies table

Revision ID: c8d5e2f4b9a3
Revises: b7d4e1f3a8c2
Create Date: 2026-06-01 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c8d5e2f4b9a3"
down_revision: str | Sequence[str] | None = "b7d4e1f3a8c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "retention_policies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("dataset_id", sa.String(36), nullable=False, index=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("mode", sa.String(50), nullable=False, server_default="retain_indefinitely"),
        sa.Column("horizon_days", sa.Integer(), nullable=True),
        sa.Column("preset", sa.String(50), nullable=False, server_default="retain_indefinitely"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("calculated_next_action_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", sa.String(36), nullable=False, server_default=""),
        sa.Column("updated_by", sa.String(36), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("retention_policies")
