"""add_frequency_minutes_to_datasets

Revision ID: e7f23d92e584
Revises: 6cb23d92e583
Create Date: 2026-05-25 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "e7f23d92e584"
down_revision: str | Sequence[str] | None = "6cb23d92e583"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("datasets", sa.Column("frequency_minutes", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("datasets", "frequency_minutes")
