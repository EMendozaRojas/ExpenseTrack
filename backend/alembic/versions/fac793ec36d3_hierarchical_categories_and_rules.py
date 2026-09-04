"""hierarchical categories and rules

Revision ID: fac793ec36d3
Revises: 95aec90d98e9
Create Date: 2026-09-04 18:00:00.000000

"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

from app.db.seed_categories import SYSTEM_RULES, seed_plan


revision: str = 'fac793ec36d3'
down_revision: str | None = '95aec90d98e9'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. new columns on categories
    op.add_column('categories', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.add_column(
        'categories',
        sa.Column('kind', sa.String(length=10), nullable=False, server_default='expense'),
    )
    op.add_column('categories', sa.Column('icon', sa.String(length=16), nullable=True))
    op.add_column('categories', sa.Column('color', sa.String(length=16), nullable=True))
    op.add_column(
        'categories',
        sa.Column('is_system', sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_foreign_key(
        'fk_categories_parent_id', 'categories', 'categories', ['parent_id'], ['id']
    )

    op.create_table(
        'categorization_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.Column('match_type', sa.String(length=20), nullable=False, server_default='contains'),
        sa.Column('pattern', sa.String(length=255), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.ForeignKeyConstraint(['category_id'], ['categories.id']),
        sa.PrimaryKeyConstraint('id'),
    )

    bind = op.get_bind()

    # 2. backfill is_system from owner_id
    bind.execute(sa.text('UPDATE categories SET is_system = (owner_id IS NULL)'))

    # 3. resolve name collisions within (owner_id, parent_id, kind) before adding the
    #    uniqueness index — pre-existing rows all have parent_id NULL, kind 'expense'
    duplicates = bind.execute(
        sa.text(
            """
            SELECT id, owner_id, name,
                   row_number() OVER (
                       PARTITION BY owner_id, parent_id, kind, name ORDER BY id
                   ) AS rn
            FROM categories
            """
        )
    ).all()
    for row in duplicates:
        if row.rn > 1:
            bind.execute(
                sa.text("UPDATE categories SET name = :name WHERE id = :id"),
                {"name": f"{row.name} ({row.rn})", "id": row.id},
            )

    # 4. seed system categories (Apéndice A)
    root_ids: dict[tuple[str, str], int] = {}
    for kind, root, color in seed_plan():
        root_id = bind.execute(
            sa.text(
                """
                INSERT INTO categories (name, owner_id, parent_id, kind, icon, color, is_system)
                VALUES (:name, NULL, NULL, :kind, :icon, :color, true)
                RETURNING id
                """
            ),
            {"name": root.name, "kind": kind, "icon": root.icon, "color": color},
        ).scalar_one()
        root_ids[(kind, root.name)] = root_id
        for sub_name in root.subcategories:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO categories (name, owner_id, parent_id, kind, is_system)
                    VALUES (:name, NULL, :parent_id, :kind, true)
                    """
                ),
                {"name": sub_name, "parent_id": root_id, "kind": kind},
            )

    # 5. seed system rules (Apéndice B) — all reference expense subcategories
    for patterns, root_name, sub_name in SYSTEM_RULES:
        root_id = root_ids[("expense", root_name)]
        category_id = bind.execute(
            sa.text(
                "SELECT id FROM categories WHERE parent_id = :parent_id AND name = :name"
            ),
            {"parent_id": root_id, "name": sub_name},
        ).scalar_one()
        for pattern in patterns:
            bind.execute(
                sa.text(
                    """
                    INSERT INTO categorization_rules
                        (owner_id, match_type, pattern, category_id, priority, is_enabled)
                    VALUES (NULL, 'contains', :pattern, :category_id, 0, true)
                    """
                ),
                {"pattern": pattern, "category_id": category_id},
            )

    # 6. uniqueness: NULL-safe via COALESCE sentinel (-1 is never a real id)
    op.execute(
        """
        CREATE UNIQUE INDEX ux_categories_scope_name
        ON categories (COALESCE(owner_id, -1), COALESCE(parent_id, -1), kind, name)
        """
    )

    op.alter_column('categories', 'kind', server_default=None)
    op.alter_column('categories', 'is_system', server_default=None)


def downgrade() -> None:
    op.execute('DROP INDEX ux_categories_scope_name')
    op.drop_table('categorization_rules')
    op.execute("DELETE FROM categories WHERE is_system = true")
    op.drop_constraint('fk_categories_parent_id', 'categories', type_='foreignkey')
    op.drop_column('categories', 'is_system')
    op.drop_column('categories', 'color')
    op.drop_column('categories', 'icon')
    op.drop_column('categories', 'kind')
    op.drop_column('categories', 'parent_id')
