"""add test_status to connections

Revision ID: 8e71d3f9b4a0
Revises: 6cb23d92e583
Create Date: 2026-05-21 10:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "8e71d3f9b4a0"
down_revision: Union[str, Sequence[str], None] = "6cb23d92e583"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "connections",
        sa.Column("test_status", sa.String(50), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("connections", "test_status")
