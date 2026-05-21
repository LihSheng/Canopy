"""add_real_time_strategy

Revision ID: 6cb23d92e583
Revises: 5da19c7c8118
Create Date: 2026-05-20 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "6cb23d92e583"
down_revision: str | Sequence[str] | None = "5da19c7c8118"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("datasets", sa.Column("real_time_strategy", sa.String(50), nullable=True))


def downgrade() -> None:
    op.drop_column("datasets", "real_time_strategy")
