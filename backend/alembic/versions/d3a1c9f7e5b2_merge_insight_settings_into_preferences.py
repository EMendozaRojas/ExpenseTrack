"""merge insight_settings into user_preferences

Revision ID: d3a1c9f7e5b2
Revises: c04b314435ed
Create Date: 2026-09-30 00:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = 'd3a1c9f7e5b2'
down_revision: str | None = 'c04b314435ed'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        'user_preferences',
        sa.Column('ant_max_amount', sa.Numeric(14, 2), nullable=False, server_default='10.00'),
    )
    op.add_column(
        'user_preferences',
        sa.Column('ant_min_occurrences', sa.Integer(), nullable=False, server_default='5'),
    )
    op.add_column(
        'user_preferences',
        sa.Column('ant_min_aggregate', sa.Numeric(14, 2), nullable=False, server_default='30.00'),
    )

    # Usuarios con insight_settings pero sin user_preferences todavía: crear la fila.
    op.execute(
        """
        INSERT INTO user_preferences (owner_id, base_currency, locale, ant_max_amount, ant_min_occurrences, ant_min_aggregate)
        SELECT s.owner_id, 'EUR', 'es-ES', s.ant_max_amount, s.ant_min_occurrences, s.ant_min_aggregate
        FROM insight_settings s
        WHERE NOT EXISTS (
            SELECT 1 FROM user_preferences p WHERE p.owner_id = s.owner_id
        )
        """
    )

    # Usuarios con ambas filas: copiar los umbrales de insight_settings.
    op.execute(
        """
        UPDATE user_preferences p
        SET ant_max_amount = s.ant_max_amount,
            ant_min_occurrences = s.ant_min_occurrences,
            ant_min_aggregate = s.ant_min_aggregate
        FROM insight_settings s
        WHERE p.owner_id = s.owner_id
        """
    )

    op.drop_table('insight_settings')

    op.alter_column('user_preferences', 'ant_max_amount', server_default=None)
    op.alter_column('user_preferences', 'ant_min_occurrences', server_default=None)
    op.alter_column('user_preferences', 'ant_min_aggregate', server_default=None)


def downgrade() -> None:
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

    op.execute(
        """
        INSERT INTO insight_settings (owner_id, ant_max_amount, ant_min_occurrences, ant_min_aggregate)
        SELECT owner_id, ant_max_amount, ant_min_occurrences, ant_min_aggregate
        FROM user_preferences
        """
    )

    op.drop_column('user_preferences', 'ant_max_amount')
    op.drop_column('user_preferences', 'ant_min_occurrences')
    op.drop_column('user_preferences', 'ant_min_aggregate')
