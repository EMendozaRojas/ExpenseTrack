"""user profile: full_name, avatar

Revision ID: a7c21e4f9b6d
Revises: d3a1c9f7e5b2
Create Date: 2026-10-02 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = 'a7c21e4f9b6d'
down_revision: str | None = 'd3a1c9f7e5b2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('users', sa.Column('full_name', sa.String(length=120), nullable=True))
    op.add_column('users', sa.Column('avatar_storage_key', sa.String(length=255), nullable=True))
    op.add_column('users', sa.Column('avatar_mime_type', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'avatar_mime_type')
    op.drop_column('users', 'avatar_storage_key')
    op.drop_column('users', 'full_name')
