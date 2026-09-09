"""multi-currency: user_preferences, fx_rates, transaction currency

Sin fetch automático diario del BCE en esta versión: las tasas se cargan
manualmente vía POST /fx-rates.

Revision ID: c98e19e7d24f
Revises: 09e6f82f4c15
Create Date: 2026-09-10 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = 'c98e19e7d24f'
down_revision: str | None = '09e6f82f4c15'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'user_preferences',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('base_currency', sa.String(length=3), nullable=False, server_default='EUR'),
        sa.Column('locale', sa.String(length=10), nullable=False, server_default='es-ES'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', name='ux_user_preferences_owner'),
    )
    op.alter_column('user_preferences', 'base_currency', server_default=None)
    op.alter_column('user_preferences', 'locale', server_default=None)

    op.create_table(
        'fx_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('rate_date', sa.Date(), nullable=False),
        sa.Column('base', sa.String(length=3), nullable=False),
        sa.Column('quote', sa.String(length=3), nullable=False),
        sa.Column('rate', sa.Numeric(18, 6), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('rate_date', 'base', 'quote', name='ux_fx_rates_date_pair'),
    )

    op.add_column(
        'transactions',
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='EUR'),
    )
    op.add_column(
        'transactions', sa.Column('fx_rate_to_account_currency', sa.Numeric(18, 6), nullable=True)
    )
    op.add_column(
        'transactions', sa.Column('amount_in_account_currency', sa.Numeric(14, 2), nullable=True)
    )
    op.execute('UPDATE transactions SET amount_in_account_currency = amount')
    op.alter_column('transactions', 'currency', server_default=None)


def downgrade() -> None:
    op.drop_column('transactions', 'amount_in_account_currency')
    op.drop_column('transactions', 'fx_rate_to_account_currency')
    op.drop_column('transactions', 'currency')
    op.drop_table('fx_rates')
    op.drop_table('user_preferences')
