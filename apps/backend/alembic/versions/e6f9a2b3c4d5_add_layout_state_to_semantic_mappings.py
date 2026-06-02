"""add layout_state json column to semantic_mappings

Revision ID: e6f9a2b3c4d5
Revises: d5e8f1a2b3c4
Create Date: 2026-06-02 12:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e6f9a2b3c4d5"
down_revision: str | Sequence[str] | None = "d5e8f1a2b3c4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "semantic_mappings",
        sa.Column("layout_state", sa.JSON(), nullable=False, server_default=sa.text("'{}'::json")),
    )


def downgrade() -> None:
    op.drop_column("semantic_mappings", "layout_state")
