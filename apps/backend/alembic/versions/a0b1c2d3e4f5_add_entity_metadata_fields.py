"""add entity metadata fields

Revision ID: a0b1c2d3e4f5
Revises: d6e7f8a9b0c1
Create Date: 2026-06-04 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "a0b1c2d3e4f5"
down_revision: str | Sequence[str] | None = "d6e7f8a9b0c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "semantic_object_types",
        sa.Column("plural_name", sa.String(255), nullable=False, server_default=""),
    )
    op.add_column(
        "semantic_object_types",
        sa.Column("icon", sa.String(100), nullable=False, server_default=""),
    )
    op.add_column(
        "semantic_object_types",
        sa.Column("groups", sa.JSON(), nullable=False, server_default=sa.text("'[]'")),
    )
    op.add_column(
        "semantic_object_types",
        sa.Column(
            "status",
            sa.String(50),
            nullable=False,
            server_default="in_progress",
        ),
    )
    op.create_index(
        "ix_semantic_object_types_status",
        "semantic_object_types",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_semantic_object_types_status", table_name="semantic_object_types")
    op.drop_column("semantic_object_types", "status")
    op.drop_column("semantic_object_types", "groups")
    op.drop_column("semantic_object_types", "icon")
    op.drop_column("semantic_object_types", "plural_name")
