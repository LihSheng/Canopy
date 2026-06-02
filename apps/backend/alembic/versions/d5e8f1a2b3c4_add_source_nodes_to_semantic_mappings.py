"""add source_nodes json column to semantic_mappings

Revision ID: d5e8f1a2b3c4
Revises: c8d5e2f4b9a3
Create Date: 2026-06-02 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d5e8f1a2b3c4"
down_revision: str | Sequence[str] | None = "c8d5e2f4b9a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "semantic_mappings",
        sa.Column("source_nodes", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )


def downgrade() -> None:
    op.drop_column("semantic_mappings", "source_nodes")
