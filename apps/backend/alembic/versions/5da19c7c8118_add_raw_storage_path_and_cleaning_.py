"""add_raw_storage_path_and_cleaning_issues_to_dataset_versions

Revision ID: 5da19c7c8118
Revises: a9eb23d92c20
Create Date: 2026-05-18 17:05:11.733205

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "5da19c7c8118"
down_revision: str | Sequence[str] | None = "a9eb23d92c20"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("dataset_versions", sa.Column("raw_storage_path", sa.String(500), nullable=False, server_default=""))
    op.add_column(
        "dataset_versions",
        sa.Column("cleaning_issues", sa.JSON(), nullable=False, server_default=sa.text("'[]'::json")),
    )


def downgrade() -> None:
    op.drop_column("dataset_versions", "cleaning_issues")
    op.drop_column("dataset_versions", "raw_storage_path")
