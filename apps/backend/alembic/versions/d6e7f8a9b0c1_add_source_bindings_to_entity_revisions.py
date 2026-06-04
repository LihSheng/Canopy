"""Add source_bindings JSON column to entity_revisions.

Revision ID: d6e7f8a9b0c1
Revises: c4e5f6a7b8d9
Create Date: 2026-06-04
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "d6e7f8a9b0c1"
down_revision: str | None = "c4e5f6a7b8d9"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "entity_revisions",
        sa.Column(
            "source_bindings",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("entity_revisions", "source_bindings")
