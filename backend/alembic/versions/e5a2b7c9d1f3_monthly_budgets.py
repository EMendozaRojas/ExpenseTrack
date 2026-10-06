"""monthly budgets: series + budget_months, avisos por categoría

Revision ID: e5a2b7c9d1f3
Revises: c3e7a0f5d9b4
Create Date: 2026-10-06 00:00:00.000000

"""
from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = 'e5a2b7c9d1f3'
down_revision: str | None = 'c3e7a0f5d9b4'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

BUDGET_ALERT_TYPES = "('budget_warning', 'budget_exceeded')"


def upgrade() -> None:
    op.add_column('budgets', sa.Column('starts_on', sa.Date(), nullable=True))
    op.add_column('budgets', sa.Column('ends_on', sa.Date(), nullable=True))
    op.add_column('budgets', sa.Column('category_name', sa.String(length=100), nullable=True))

    # Los presupuestos existentes pasan a ser series que empiezan el mes en
    # que se crearon; los pausados terminan en el mes en curso (y si además
    # empezaron este mes, no tienen historial y se eliminan).
    op.execute(
        """
        UPDATE budgets b
        SET starts_on = date_trunc('month', b.created_at)::date,
            category_name = c.name
        FROM categories c
        WHERE c.id = b.category_id
        """
    )
    op.execute(
        """
        UPDATE budgets
        SET ends_on = date_trunc('month', now())::date
        WHERE is_active = false
        """
    )

    # Los avisos de presupuesto pasan a identificarse por categoría (no por
    # presupuesto): un aviso por (categoría, tipo, mes). Como había como mucho
    # un presupuesto por categoría, el remapeo no puede crear duplicados.
    op.execute(
        f"""
        UPDATE notifications n
        SET related_id = b.category_id
        FROM budgets b
        WHERE n.type IN {BUDGET_ALERT_TYPES} AND n.related_id = b.id
        """
    )
    op.execute("DELETE FROM budgets WHERE ends_on IS NOT NULL AND ends_on <= starts_on")

    op.alter_column('budgets', 'starts_on', nullable=False)
    op.alter_column('budgets', 'category_name', nullable=False)
    op.drop_column('budgets', 'is_active')
    op.drop_constraint('ux_budgets_owner_category', 'budgets', type_='unique')
    op.drop_constraint('budgets_category_id_fkey', 'budgets', type_='foreignkey')
    op.alter_column('budgets', 'category_id', nullable=True)
    op.create_foreign_key(
        'budgets_category_id_fkey', 'budgets', 'categories', ['category_id'], ['id'],
        ondelete='SET NULL',
    )
    op.create_index('ix_budgets_owner_category', 'budgets', ['owner_id', 'category_id'])

    op.create_table(
        'budget_months',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.Column('category_name', sa.String(length=100), nullable=False),
        sa.Column('month', sa.Date(), nullable=False),
        sa.Column('kind', sa.String(length=10), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=True),
        sa.Column('frozen_spent', sa.Numeric(14, 2), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'owner_id', 'category_id', 'month', name='ux_budget_months_owner_category_month'
        ),
    )
    op.create_index('ix_budget_months_owner_month', 'budget_months', ['owner_id', 'month'])


def downgrade() -> None:
    # Se reconstruye un presupuesto por categoría a partir de la serie vigente
    # en el mes en curso (o la más reciente); los montos por mes se pierden.
    op.drop_index('ix_budget_months_owner_month', table_name='budget_months')
    op.drop_table('budget_months')

    op.execute("DELETE FROM budgets WHERE category_id IS NULL")
    op.execute(
        """
        DELETE FROM budgets
        WHERE id NOT IN (
            SELECT DISTINCT ON (owner_id, category_id) id
            FROM budgets
            ORDER BY owner_id, category_id, (ends_on IS NULL) DESC, starts_on DESC
        )
        """
    )
    op.add_column(
        'budgets', sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true())
    )
    op.execute(
        """
        UPDATE budgets SET is_active = false
        WHERE ends_on IS NOT NULL AND ends_on <= date_trunc('month', now())::date
        """
    )
    op.alter_column('budgets', 'is_active', server_default=None)
    op.execute(
        f"""
        UPDATE notifications n
        SET related_id = b.id
        FROM budgets b
        WHERE n.type IN {BUDGET_ALERT_TYPES}
          AND n.related_id = b.category_id
          AND n.owner_id = b.owner_id
        """
    )
    op.execute(
        "DELETE FROM notifications "
        "WHERE type IN ('budget_month_summary', 'budget_category_deleted')"
    )

    op.drop_index('ix_budgets_owner_category', table_name='budgets')
    op.drop_constraint('budgets_category_id_fkey', 'budgets', type_='foreignkey')
    op.alter_column('budgets', 'category_id', nullable=False)
    op.create_foreign_key(
        'budgets_category_id_fkey', 'budgets', 'categories', ['category_id'], ['id']
    )
    op.create_unique_constraint('ux_budgets_owner_category', 'budgets', ['owner_id', 'category_id'])
    op.drop_column('budgets', 'category_name')
    op.drop_column('budgets', 'ends_on')
    op.drop_column('budgets', 'starts_on')
