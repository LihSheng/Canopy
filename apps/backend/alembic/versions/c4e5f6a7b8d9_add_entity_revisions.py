"""add entity_revisions and entity_revision_dependencies tables

Revision ID: c4e5f6a7b8d9
Revises: b3d4e5f6a7c8
Create Date: 2026-06-03 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "c4e5f6a7b8d9"
down_revision: str | Sequence[str] | None = "b3d4e5f6a7c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── entity_revisions ──
    op.create_table(
        "entity_revisions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("entity_id", sa.String(36), sa.ForeignKey("semantic_object_types.id"), nullable=False, index=True),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="draft",
            comment="draft | published | archived",
        ),
        sa.Column("forked_from_revision_id", sa.String(36), nullable=True),
        sa.Column(
            "properties",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
            comment="Canonical entity properties with stable property_ids",
        ),
        sa.Column(
            "links",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column(
            "source_nodes",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column(
            "computed_properties",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'[]'::json"),
        ),
        sa.Column(
            "layout_state",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column("lock_holder_id", sa.String(36), nullable=True, comment="User ID holding the draft lock"),
        sa.Column("locked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("entity_id", "revision_number", name="uq_entity_revision_number"),
    )
    op.create_index("ix_entity_revisions_status", "entity_revisions", ["status"], unique=False)
    op.create_index(
        "ix_entity_revisions_entity_status",
        "entity_revisions",
        ["entity_id", "status"],
        unique=False,
    )

    # ── entity_revision_dependencies ──
    op.create_table(
        "entity_revision_dependencies",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "revision_id",
            sa.String(36),
            sa.ForeignKey("entity_revisions.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "dependency_type",
            sa.String(20),
            nullable=False,
            comment="dataset | dataset_version",
        ),
        sa.Column("dependency_id", sa.String(36), nullable=False),
        sa.UniqueConstraint(
            "revision_id",
            "dependency_type",
            "dependency_id",
            name="uq_revision_dependency",
        ),
    )


def downgrade() -> None:
    op.drop_table("entity_revision_dependencies")
    op.drop_table("entity_revisions")
