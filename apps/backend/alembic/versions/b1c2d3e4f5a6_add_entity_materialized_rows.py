"""add entity_materialized_rows table

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-06-09 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "b1c2d3e4f5a6"
down_revision: str | Sequence[str] | None = "a0b1c2d3e4f5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "entity_materialized_rows",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), sa.ForeignKey("semantic_object_types.id"), nullable=False, index=True),
        sa.Column("revision_id", sa.String(36), sa.ForeignKey("entity_revisions.id"), nullable=False, index=True),
        sa.Column("row_id", sa.String(255), nullable=False, index=True),
        sa.Column("row_data", sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column("is_tombstone", sa.Boolean(), nullable=False, server_default=sa.text("false"), index=True),
        sa.Column(
            "materialized_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("entity_materialized_rows")
