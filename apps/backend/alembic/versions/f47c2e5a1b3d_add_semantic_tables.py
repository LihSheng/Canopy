"""add semantic mapping and object type tables

Revision ID: f47c2e5a1b3d
Revises: 8e71d3f9b4a0
Create Date: 2026-05-29 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "f47c2e5a1b3d"
down_revision: str | Sequence[str] | None = "8e71d3f9b4a0"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "semantic_object_types",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("object_type_key", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("tenant_id", "object_type_key", name="uq_object_type_key_per_tenant"),
    )

    op.create_table(
        "semantic_mappings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("dataset_id", sa.String(36), nullable=False, index=True),
        sa.Column("dataset_version_id", sa.String(36), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("object_type_id", sa.String(36), nullable=False),
        sa.Column("object_type_key", sa.String(255), nullable=False),
        sa.Column("properties", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.ForeignKeyConstraint(
            ["object_type_id"],
            ["semantic_object_types.id"],
        ),
        sa.UniqueConstraint(
            "dataset_id",
            "dataset_version_id",
            "version_number",
            name="uq_mapping_version",
        ),
    )


def downgrade() -> None:
    op.drop_table("semantic_mappings")
    op.drop_table("semantic_object_types")
