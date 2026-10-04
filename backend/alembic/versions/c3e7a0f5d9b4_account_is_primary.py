"""accounts: is_primary

Revision ID: c3e7a0f5d9b4
Revises: b8f4d2c6a1e3
Create Date: 2026-10-04 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = 'c3e7a0f5d9b4'
down_revision: str | None = 'b8f4d2c6a1e3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('accounts', sa.Column('is_primary', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.alter_column('accounts', 'is_primary', server_default=None)


def downgrade() -> None:
    op.drop_column('accounts', 'is_primary')
