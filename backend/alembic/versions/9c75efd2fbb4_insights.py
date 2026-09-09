"""insights: recurring dismiss log + ant-spending settings

Revision ID: 9c75efd2fbb4
Revises: 8bef1847415b
Create Date: 2026-09-10 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = '9c75efd2fbb4'
down_revision: str | None = '8bef1847415b'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'insight_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('ant_max_amount', sa.Numeric(14, 2), nullable=False, server_default='10.00'),
        sa.Column('ant_min_occurrences', sa.Integer(), nullable=False, server_default='5'),
        sa.Column('ant_min_aggregate', sa.Numeric(14, 2), nullable=False, server_default='30.00'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', name='ux_insight_settings_owner'),
    )
    op.alter_column('insight_settings', 'ant_max_amount', server_default=None)
    op.alter_column('insight_settings', 'ant_min_occurrences', server_default=None)
    op.alter_column('insight_settings', 'ant_min_aggregate', server_default=None)

    op.create_table(
        'dismissed_recurring_series',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('series_key', sa.String(length=300), nullable=False),
        sa.Column('dismissed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', 'series_key', name='ux_dismissed_recurring_owner_key'),
    )


def downgrade() -> None:
    op.drop_table('dismissed_recurring_series')
    op.drop_table('insight_settings')
