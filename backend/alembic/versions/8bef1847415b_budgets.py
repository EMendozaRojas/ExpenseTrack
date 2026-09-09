"""budgets (tope mensual por categoría, sin rollover ni alertas persistidas)

Revision ID: 8bef1847415b
Revises: 5d286718e41d
Create Date: 2026-09-10 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = '8bef1847415b'
down_revision: str | None = '5d286718e41d'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        'budgets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', 'category_id', name='ux_budgets_owner_category'),
    )
    op.alter_column('budgets', 'is_active', server_default=None)


def downgrade() -> None:
    op.drop_table('budgets')
