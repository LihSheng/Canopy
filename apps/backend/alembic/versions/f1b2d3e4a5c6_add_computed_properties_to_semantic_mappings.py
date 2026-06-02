"""add computed_properties json column to semantic_mappings

Revision ID: f1b2d3e4a5c6
Revises: e6f9a2b3c4d5
Create Date: 2026-06-02 15:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f1b2d3e4a5c6"
down_revision: str | Sequence[str] | None = "e6f9a2b3c4d5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "semantic_mappings",
        sa.Column("computed_properties", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )


def downgrade() -> None:
    op.drop_column("semantic_mappings", "computed_properties")
