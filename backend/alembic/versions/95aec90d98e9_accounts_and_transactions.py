"""accounts and transactions

Revision ID: 95aec90d98e9
Revises: 992f793be938
Create Date: 2026-09-04 17:11:22.956084

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '95aec90d98e9'
down_revision: str | None = '992f793be938'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. accounts table
    op.create_table(
        'accounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=False, server_default='EUR'),
        sa.Column('initial_balance', sa.Numeric(precision=14, scale=2), nullable=False, server_default='0'),
        sa.Column('is_archived', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    # 2. widen amount precision before renaming table
    op.alter_column(
        'expenses', 'amount',
        existing_type=sa.Numeric(precision=10, scale=2),
        type_=sa.Numeric(precision=14, scale=2),
        existing_nullable=False,
    )

    # 3. new columns on the (still named) expenses table
    op.add_column('expenses', sa.Column('direction', sa.String(length=10), nullable=False, server_default='expense'))
    op.add_column('expenses', sa.Column('account_id', sa.Integer(), nullable=True))
    op.add_column('expenses', sa.Column('counterparty', sa.String(length=255), nullable=True))
    op.add_column('expenses', sa.Column('raw_description', sa.String(length=255), nullable=True))
    op.add_column('expenses', sa.Column('source', sa.String(length=10), nullable=False, server_default='manual'))
    op.add_column('expenses', sa.Column('transfer_group_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('expenses', sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
    op.add_column('expenses', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))

    # 4. rename columns
    op.alter_column('expenses', 'expense_date', new_column_name='posted_at')
    op.alter_column('expenses', 'description', new_column_name='note')

    # 5. category_id becomes optional
    op.alter_column('expenses', 'category_id', existing_type=sa.Integer(), nullable=True)

    # 6. rename table
    op.rename_table('expenses', 'transactions')

    # 7. data migration: one "Efectivo" cash account per existing owner, backfill account_id,
    #    flip the sign of the migrated amounts (previously stored positive)
    bind = op.get_bind()
    owner_ids = bind.execute(sa.text('SELECT DISTINCT owner_id FROM transactions')).scalars().all()
    for owner_id in owner_ids:
        account_id = bind.execute(
            sa.text(
                """
                INSERT INTO accounts (owner_id, name, type, currency, initial_balance, is_archived)
                VALUES (:owner_id, 'Efectivo', 'cash', 'EUR', 0, false)
                RETURNING id
                """
            ),
            {"owner_id": owner_id},
        ).scalar_one()
        bind.execute(
            sa.text(
                """
                UPDATE transactions
                SET account_id = :account_id, amount = -amount
                WHERE owner_id = :owner_id
                """
            ),
            {"account_id": account_id, "owner_id": owner_id},
        )

    # 8. account_id is required from here on
    op.alter_column('transactions', 'account_id', existing_type=sa.Integer(), nullable=False)

    # 9. foreign keys + indexes
    op.create_foreign_key(
        'fk_transactions_account_id', 'transactions', 'accounts', ['account_id'], ['id']
    )
    op.create_index(
        'ix_transactions_owner_posted',
        'transactions',
        ['owner_id', 'posted_at'],
        postgresql_where=sa.text('deleted_at IS NULL'),
    )
    op.create_index('ix_transactions_account_posted', 'transactions', ['account_id', 'posted_at'])
    op.create_index('ix_transactions_transfer_group', 'transactions', ['transfer_group_id'])

    # defaults were only needed to backfill existing rows; the app always supplies these going forward
    op.alter_column('transactions', 'direction', server_default=None)
    op.alter_column('transactions', 'source', server_default=None)


def downgrade() -> None:
    op.drop_index('ix_transactions_transfer_group', table_name='transactions')
    op.drop_index('ix_transactions_account_posted', table_name='transactions')
    op.drop_index('ix_transactions_owner_posted', table_name='transactions')
    op.drop_constraint('fk_transactions_account_id', 'transactions', type_='foreignkey')

    bind = op.get_bind()
    bind.execute(sa.text('UPDATE transactions SET amount = -amount'))

    op.alter_column('transactions', 'category_id', existing_type=sa.Integer(), nullable=False)
    op.alter_column('transactions', 'posted_at', new_column_name='expense_date')
    op.alter_column('transactions', 'note', new_column_name='description')

    op.drop_column('transactions', 'deleted_at')
    op.drop_column('transactions', 'updated_at')
    op.drop_column('transactions', 'transfer_group_id')
    op.drop_column('transactions', 'source')
    op.drop_column('transactions', 'raw_description')
    op.drop_column('transactions', 'counterparty')
    op.drop_column('transactions', 'account_id')
    op.drop_column('transactions', 'direction')

    op.alter_column(
        'transactions', 'amount',
        existing_type=sa.Numeric(precision=14, scale=2),
        type_=sa.Numeric(precision=10, scale=2),
        existing_nullable=False,
    )

    op.rename_table('transactions', 'expenses')
    op.drop_table('accounts')
