"""taxonomy v2 (10 raíces de gasto) + is_fixed + Sin Clasificar real

Reemplaza el seed de gasto de `fac793ec36d3` por la taxonomía v2 confirmada
en producto (Alimentación, Restauración, Vivienda, Transporte, Compras y
Personal, Suscripciones, Ocio, Salud, Familia y Mascotas, Finanzas y Otros).

Cambios de negocio que trae:
- Cada subcategoría lleva `is_fixed` (gasto fijo vs. variable para el
  Dashboard).
- "Sin Clasificar" pasa a ser una subcategoría real de sistema
  (`Finanzas y Otros > Sin Clasificar`), no `category_id NULL`. Toda
  transacción de income/expense debe apuntar a una subcategoría.
- Las transacciones y reglas que apuntaban a subcategorías antiguas se
  remapean por nombre (best-effort); lo ambiguo cae en "Sin Clasificar".

Revision ID: b5963a0e5c7c
Revises: fac793ec36d3
Create Date: 2026-09-08 00:00:00.000000

"""
from collections.abc import Sequence
from typing import NamedTuple

from alembic import op
import sqlalchemy as sa

# Datos congelados tal como estaban al escribir esta migración (commit a4203f2).
# Una migración es una foto del pasado: no importa el seed de `app/`, que puede
# cambiar después y romper `alembic upgrade head` en una BD vacía.
class _Sub(NamedTuple):
    name: str
    is_fixed: bool = False


class _Root(NamedTuple):
    name: str
    icon: str
    subcategories: list[_Sub]


EXPENSE_ROOTS: list[_Root] = [
    _Root('Alimentación', '🛒', [_Sub('Supermercado')]),
    _Root('Restauración', '🍽️', [_Sub('Restaurantes'), _Sub('Cafeterías'), _Sub('Delivery'), _Sub('Bares/Copas')]),
    _Root('Vivienda', '🏠', [_Sub('Alquiler/Hipoteca', is_fixed=True), _Sub('Suministros (Luz/Agua/Gas)', is_fixed=True), _Sub('Internet/Móvil', is_fixed=True), _Sub('Mantenimiento')]),
    _Root('Transporte', '🚌', [_Sub('Combustible'), _Sub('Transporte Público'), _Sub('Taxi/VTC'), _Sub('Mantenimiento/Parking')]),
    _Root('Compras y Personal', '🛍️', [_Sub('Ropa y Calzado'), _Sub('Tecnología'), _Sub('Hogar'), _Sub('Cuidado Personal')]),
    _Root('Suscripciones', '🔁', [_Sub('Streaming', is_fixed=True), _Sub('Software', is_fixed=True), _Sub('Gimnasio', is_fixed=True), _Sub('Servicios Recurrentes', is_fixed=True)]),
    _Root('Ocio', '🎬', [_Sub('Cine/Eventos'), _Sub('Viajes/Hoteles'), _Sub('Juegos/Aficiones')]),
    _Root('Salud', '💊', [_Sub('Farmacia'), _Sub('Médicos/Dentista')]),
    _Root('Familia y Mascotas', '👨‍👩‍👧', [_Sub('Educación', is_fixed=True), _Sub('Mascotas'), _Sub('Guardería/Colegio', is_fixed=True)]),
    _Root('Finanzas y Otros', '🏦', [_Sub('Comisiones', is_fixed=True), _Sub('Impuestos', is_fixed=True), _Sub('Sin Clasificar')]),
]

UNCATEGORIZED_EXPENSE = ('Finanzas y Otros', 'Sin Clasificar')

# (patrones, categoría raíz, subcategoría) — todas match_type='contains', owner_id NULL
SYSTEM_RULES: list[tuple[list[str], str, str]] = [
    (['MERCADONA', 'CARREFOUR', 'LIDL', 'DIA', 'ALCAMPO', 'EROSKI', 'CONSUM'], 'Alimentación', 'Supermercado'),
    (['REPSOL', 'CEPSA', 'GALP', 'BP', 'SHELL'], 'Transporte', 'Combustible'),
    (['NETFLIX', 'SPOTIFY', 'HBO', 'DISNEY', 'AMAZON PRIME', 'FILMIN'], 'Suscripciones', 'Streaming'),
    (['EMT', 'METRO', 'RENFE', 'CERCANIAS'], 'Transporte', 'Transporte Público'),
    (['FARMACIA'], 'Salud', 'Farmacia'),
    (['GLOVO', 'UBER EATS', 'JUST EAT', 'DELIVEROO'], 'Restauración', 'Delivery'),
]

# Mapa best-effort de la taxonomía original a la v2. Ambigua -> UNCATEGORIZED.
LEGACY_SUBCATEGORY_MAP: dict[str, tuple[str, str]] = {
    'Supermercado': ('Alimentación', 'Supermercado'),
    'Restaurantes': ('Restauración', 'Restaurantes'),
    'Comida a domicilio': ('Restauración', 'Delivery'),
    'Alquiler / Hipoteca': ('Vivienda', 'Alquiler/Hipoteca'),
    'Suministros (luz, agua, gas)': ('Vivienda', 'Suministros (Luz/Agua/Gas)'),
    'Internet y teléfono': ('Vivienda', 'Internet/Móvil'),
    'Mantenimiento y reparaciones': ('Vivienda', 'Mantenimiento'),
    'Seguro de hogar': ('Suscripciones', 'Servicios Recurrentes'),
    'Transporte público': ('Transporte', 'Transporte Público'),
    'Combustible': ('Transporte', 'Combustible'),
    'Parking y peajes': ('Transporte', 'Mantenimiento/Parking'),
    'Taxi / VTC': ('Transporte', 'Taxi/VTC'),
    'Mantenimiento del vehículo': ('Transporte', 'Mantenimiento/Parking'),
    'Seguro del coche': ('Suscripciones', 'Servicios Recurrentes'),
    'Impuestos e ITV': ('Finanzas y Otros', 'Impuestos'),
    'Farmacia': ('Salud', 'Farmacia'),
    'Médico y dentista': ('Salud', 'Médicos/Dentista'),
    'Seguro médico': ('Suscripciones', 'Servicios Recurrentes'),
    'Gimnasio y deporte': ('Suscripciones', 'Gimnasio'),
    'Cine, teatro y eventos': ('Ocio', 'Cine/Eventos'),
    'Libros, música y juegos': ('Ocio', 'Juegos/Aficiones'),
    'Suscripciones': ('Suscripciones', 'Streaming'),
    'Viajes y vacaciones': ('Ocio', 'Viajes/Hoteles'),
    'Aficiones': ('Ocio', 'Juegos/Aficiones'),
    'Ropa y calzado': ('Compras y Personal', 'Ropa y Calzado'),
    'Electrónica': ('Compras y Personal', 'Tecnología'),
    'Hogar y decoración': ('Compras y Personal', 'Hogar'),
    'Cuidado personal': ('Compras y Personal', 'Cuidado Personal'),
    'Matrículas y cursos': ('Familia y Mascotas', 'Educación'),
    'Material y libros': ('Familia y Mascotas', 'Educación'),
    'Idiomas': ('Familia y Mascotas', 'Educación'),
    'Comisiones bancarias': ('Finanzas y Otros', 'Comisiones'),
    'Impuestos y tasas': ('Finanzas y Otros', 'Impuestos'),
    'Comida y accesorios': ('Familia y Mascotas', 'Mascotas'),
    'Veterinario': ('Familia y Mascotas', 'Mascotas'),
    'Guardería y colegio': ('Familia y Mascotas', 'Guardería/Colegio'),
}


revision: str = 'b5963a0e5c7c'
down_revision: str | None = 'fac793ec36d3'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_PALETTE = [
    "#4F86C6", "#E4572E", "#76B041", "#F3A712", "#8E7CC3",
    "#48A9A6", "#D64550", "#3E92CC", "#6A994E", "#B56576",
]


def upgrade() -> None:
    op.add_column(
        'categories',
        sa.Column('is_fixed', sa.Boolean(), nullable=False, server_default=sa.false()),
    )

    bind = op.get_bind()

    # 1. snapshot de la taxonomía de gasto antigua (solo categorías de sistema).
    #    6 raíces coinciden de nombre con la v2 (Alimentación, Restauración,
    #    Vivienda, Transporte, Ocio, Salud): se reutiliza su id en vez de
    #    reinsertar (violaría ux_categories_scope_name). Igual por subcategoría
    #    cuando el nombre es idéntico letra a letra.
    old_roots = bind.execute(
        sa.text(
            "SELECT id, name FROM categories WHERE is_system = true AND kind = 'expense' AND parent_id IS NULL"
        )
    ).all()
    old_roots_by_name = {row.name: row.id for row in old_roots}
    old_subs = bind.execute(
        sa.text(
            """
            SELECT id, name AS sub_name, parent_id
            FROM categories
            WHERE is_system = true AND kind = 'expense' AND parent_id IS NOT NULL
            """
        )
    ).all()
    old_subs_by_parent_and_name = {(row.parent_id, row.sub_name): row.id for row in old_subs}

    kept_ids: set[int] = set()
    new_sub_ids: dict[tuple[str, str], int] = {}
    for index, root in enumerate(EXPENSE_ROOTS):
        reused_root_id = old_roots_by_name.get(root.name)
        if reused_root_id is not None:
            root_id = reused_root_id
            kept_ids.add(root_id)
        else:
            color = _PALETTE[index % len(_PALETTE)]
            root_id = bind.execute(
                sa.text(
                    """
                    INSERT INTO categories (name, owner_id, parent_id, kind, icon, color, is_system, is_fixed)
                    VALUES (:name, NULL, NULL, 'expense', :icon, :color, true, false)
                    RETURNING id
                    """
                ),
                {"name": root.name, "icon": root.icon, "color": color},
            ).scalar_one()

        for sub in root.subcategories:
            reused_sub_id = old_subs_by_parent_and_name.get((root_id, sub.name))
            if reused_sub_id is not None:
                bind.execute(
                    sa.text("UPDATE categories SET is_fixed = :is_fixed WHERE id = :id"),
                    {"is_fixed": sub.is_fixed, "id": reused_sub_id},
                )
                sub_id = reused_sub_id
                kept_ids.add(sub_id)
            else:
                sub_id = bind.execute(
                    sa.text(
                        """
                        INSERT INTO categories (name, owner_id, parent_id, kind, is_system, is_fixed)
                        VALUES (:name, NULL, :parent_id, 'expense', true, :is_fixed)
                        RETURNING id
                        """
                    ),
                    {"name": sub.name, "parent_id": root_id, "is_fixed": sub.is_fixed},
                ).scalar_one()
            new_sub_ids[(root.name, sub.name)] = sub_id

    uncategorized_id = new_sub_ids[UNCATEGORIZED_EXPENSE]

    # 2. remapear transacciones y reglas que apuntaban a subcategorías antiguas
    #    que no sobrevivieron (no reutilizadas)
    stale_subs = [row for row in old_subs if row.id not in kept_ids]
    for old in stale_subs:
        target = LEGACY_SUBCATEGORY_MAP.get(old.sub_name)
        new_id = new_sub_ids[target] if target else uncategorized_id
        bind.execute(
            sa.text("UPDATE transactions SET category_id = :new_id WHERE category_id = :old_id"),
            {"new_id": new_id, "old_id": old.id},
        )
        bind.execute(
            sa.text(
                "UPDATE categorization_rules SET category_id = :new_id WHERE category_id = :old_id"
            ),
            {"new_id": new_id, "old_id": old.id},
        )

    # 3. defensivo: algo apuntando directamente a una raíz antigua -> Sin Clasificar
    stale_roots = [row for row in old_roots if row.id not in kept_ids]
    for old in stale_roots:
        bind.execute(
            sa.text("UPDATE transactions SET category_id = :new_id WHERE category_id = :old_id"),
            {"new_id": uncategorized_id, "old_id": old.id},
        )
        bind.execute(
            sa.text(
                "UPDATE categorization_rules SET category_id = :new_id WHERE category_id = :old_id"
            ),
            {"new_id": uncategorized_id, "old_id": old.id},
        )

    # 4. las reglas de sistema antiguas se sustituyen íntegras por las de la v2
    bind.execute(sa.text("DELETE FROM categorization_rules WHERE owner_id IS NULL"))

    # 5. borrar lo que quedó de la taxonomía antigua (subcategorías no
    #    reutilizadas primero, luego raíces no reutilizadas — ya sin hijos)
    stale_sub_ids = [row.id for row in stale_subs]
    if stale_sub_ids:
        bind.execute(sa.text("DELETE FROM categories WHERE id = ANY(:ids)"), {"ids": stale_sub_ids})
    stale_root_ids = [row.id for row in stale_roots]
    if stale_root_ids:
        bind.execute(sa.text("DELETE FROM categories WHERE id = ANY(:ids)"), {"ids": stale_root_ids})

    # 7. backfill de category_id NULL heredado (income/expense siempre deben llevar uno)
    income_uncategorized_id = bind.execute(
        sa.text(
            """
            SELECT c.id FROM categories c
            JOIN categories p ON p.id = c.parent_id
            WHERE c.is_system = true AND p.name = 'Otros ingresos' AND c.name = 'Sin clasificar'
            """
        )
    ).scalar_one()
    bind.execute(
        sa.text(
            "UPDATE transactions SET category_id = :id WHERE category_id IS NULL AND direction = 'expense'"
        ),
        {"id": uncategorized_id},
    )
    bind.execute(
        sa.text(
            "UPDATE transactions SET category_id = :id WHERE category_id IS NULL AND direction = 'income'"
        ),
        {"id": income_uncategorized_id},
    )

    # 8. reglas de sistema v2
    for patterns, root_name, sub_name in SYSTEM_RULES:
        category_id = new_sub_ids[(root_name, sub_name)]
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

    op.alter_column('categories', 'is_fixed', server_default=None)


def downgrade() -> None:
    # Downgrade con pérdida de datos (mismo precedente que fac793ec36d3): las
    # transacciones remapeadas a la taxonomía v2 no vuelven a su categoría
    # original, quedan sin categorizar.
    bind = op.get_bind()
    bind.execute(sa.text("DELETE FROM categorization_rules WHERE owner_id IS NULL"))
    bind.execute(
        sa.text(
            """
            UPDATE transactions SET category_id = NULL
            WHERE category_id IN (
                SELECT id FROM categories WHERE is_system = true AND kind = 'expense'
            )
            """
        )
    )
    bind.execute(sa.text("DELETE FROM categories WHERE is_system = true AND kind = 'expense'"))
    op.drop_column('categories', 'is_fixed')
