"""bank statement import (CSV, primer corte)

Revision ID: 5d286718e41d
Revises: b5963a0e5c7c
Create Date: 2026-09-09 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = '5d286718e41d'
down_revision: str | None = 'b5963a0e5c7c'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'import_batches',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='previewed'),
        sa.Column('range_start', sa.Date(), nullable=False),
        sa.Column('range_end', sa.Date(), nullable=False),
        sa.Column('strategy', sa.String(length=20), nullable=True),
        sa.Column('inserted_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('replaced_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('skipped_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('committed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    op.create_table(
        'import_rows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('batch_id', sa.Integer(), nullable=False),
        sa.Column('posted_at', sa.Date(), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('raw_description', sa.String(length=255), nullable=False),
        sa.Column('external_hash', sa.String(length=64), nullable=False),
        sa.Column('classification', sa.String(length=20), nullable=False),
        sa.Column('matched_transaction_id', sa.Integer(), nullable=True),
        sa.Column('created_transaction_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['batch_id'], ['import_batches.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['matched_transaction_id'], ['transactions.id']),
        sa.ForeignKeyConstraint(['created_transaction_id'], ['transactions.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_import_rows_batch_id', 'import_rows', ['batch_id'])

    op.alter_column('import_batches', 'status', server_default=None)
    op.alter_column('import_batches', 'inserted_count', server_default=None)
    op.alter_column('import_batches', 'replaced_count', server_default=None)
    op.alter_column('import_batches', 'skipped_count', server_default=None)


def downgrade() -> None:
    op.drop_index('ix_import_rows_batch_id', table_name='import_rows')
    op.drop_table('import_rows')
    op.drop_table('import_batches')
