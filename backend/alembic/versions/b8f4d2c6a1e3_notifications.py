"""notifications (presupuestos y metas)

Revision ID: b8f4d2c6a1e3
Revises: a7c21e4f9b6d
Create Date: 2026-10-04 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = 'b8f4d2c6a1e3'
down_revision: str | None = 'a7c21e4f9b6d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=30), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('body', sa.String(length=500), nullable=False),
        sa.Column('related_id', sa.Integer(), nullable=False),
        sa.Column('period_key', sa.String(length=10), nullable=False, server_default=''),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', 'type', 'related_id', 'period_key', name='ux_notifications_dedupe'),
    )
    op.alter_column('notifications', 'period_key', server_default=None)
    op.alter_column('notifications', 'is_read', server_default=None)
    op.create_index('ix_notifications_owner_id', 'notifications', ['owner_id'])


def downgrade() -> None:
    op.drop_index('ix_notifications_owner_id', table_name='notifications')
    op.drop_table('notifications')
