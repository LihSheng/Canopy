"""add feature_flags table for global on/off rollout controls

Revision ID: a2c3d4e5f6a7
Revises: f1b2d3e4a5c6
Create Date: 2026-06-02 16:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a2c3d4e5f6a7"
down_revision: str | Sequence[str] | None = "f1b2d3e4a5c6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "feature_flags",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("flag_key", sa.String(255), nullable=False, unique=True, index=True),
        sa.Column("description", sa.Text(), nullable=False, server_default=sa.text("''")),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )


def downgrade() -> None:
    op.drop_table("feature_flags")
