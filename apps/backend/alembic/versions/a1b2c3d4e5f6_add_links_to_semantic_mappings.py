"""add links json column to semantic_mappings

Revision ID: a1b2c3d4e5f6
Revises: f47c2e5a1b3d
Create Date: 2026-05-29 11:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: str | Sequence[str] | None = "f47c2e5a1b3d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "semantic_mappings",
        sa.Column("links", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )


def downgrade() -> None:
    op.drop_column("semantic_mappings", "links")
