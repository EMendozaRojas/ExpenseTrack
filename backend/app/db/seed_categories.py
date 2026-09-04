"""Seed de categorías y reglas de sistema (Apéndices A y B de
openspec/changes/hierarchical-categories-and-rules/design.md).

Estructura versionada y reutilizada por la data-migration de Alembic.
"""

from dataclasses import dataclass, field

_PALETTE = [
    "#4F86C6", "#E4572E", "#76B041", "#F3A712", "#8E7CC3",
    "#48A9A6", "#D64550", "#3E92CC", "#6A994E", "#B56576",
    "#457B9D", "#E07A5F",
]


@dataclass(frozen=True)
class SeedRoot:
    name: str
    icon: str
    subcategories: list[str] = field(default_factory=list)


EXPENSE_ROOTS: list[SeedRoot] = [
    SeedRoot("Vivienda", "🏠", [
        "Alquiler / Hipoteca", "Comunidad", "Suministros (luz, agua, gas)",
        "Internet y teléfono", "Mantenimiento y reparaciones", "Seguro de hogar",
    ]),
    SeedRoot("Alimentación", "🛒", ["Supermercado", "Mercado y panadería"]),
    SeedRoot("Restauración", "🍽️", ["Restaurantes", "Bares y cafeterías", "Comida a domicilio"]),
    SeedRoot("Transporte", "🚌", [
        "Transporte público", "Combustible", "Parking y peajes", "Taxi / VTC",
        "Mantenimiento del vehículo", "Seguro del coche", "Impuestos e ITV",
    ]),
    SeedRoot("Salud", "💊", [
        "Farmacia", "Médico y dentista", "Seguro médico", "Óptica", "Gimnasio y deporte",
    ]),
    SeedRoot("Ocio", "🎬", [
        "Cine, teatro y eventos", "Libros, música y juegos", "Suscripciones",
        "Viajes y vacaciones", "Aficiones",
    ]),
    SeedRoot("Compras", "🛍️", [
        "Ropa y calzado", "Electrónica", "Hogar y decoración", "Cuidado personal", "Regalos",
    ]),
    SeedRoot("Educación", "🎓", ["Matrículas y cursos", "Material y libros", "Idiomas"]),
    SeedRoot("Finanzas", "🏦", [
        "Comisiones bancarias", "Intereses de préstamos", "Impuestos y tasas", "Asesoría",
    ]),
    SeedRoot("Mascotas", "🐾", ["Comida y accesorios", "Veterinario"]),
    SeedRoot(
        "Familia e hijos", "👨‍👩‍👧",
        ["Guardería y colegio", "Ropa y juguetes", "Actividades"],
    ),
    SeedRoot("Otros gastos", "📦", ["Retiradas de efectivo", "Donativos", "Sin clasificar"]),
]

INCOME_ROOTS: list[SeedRoot] = [
    SeedRoot("Nómina y salario", "💼", ["Nómina", "Pagas extra", "Bonus"]),
    SeedRoot("Trabajo autónomo", "🧾", ["Facturas a clientes"]),
    SeedRoot("Rendimientos", "📈", ["Intereses", "Dividendos", "Alquileres cobrados"]),
    SeedRoot("Reembolsos", "↩️", [
        "Devoluciones de compras", "Devolución de Hacienda", "Gastos compartidos",
    ]),
    SeedRoot("Ayudas y prestaciones", "🤝", ["Subvenciones", "Prestaciones"]),
    SeedRoot("Otros ingresos", "💰", ["Regalos recibidos", "Sin clasificar"]),
]


def seed_plan() -> list[tuple[str, SeedRoot, str]]:
    """Devuelve (kind, root, color) para cada raíz, en orden estable."""
    plan = []
    index = 0
    for root in EXPENSE_ROOTS:
        plan.append(("expense", root, _PALETTE[index % len(_PALETTE)]))
        index += 1
    for root in INCOME_ROOTS:
        plan.append(("income", root, _PALETTE[index % len(_PALETTE)]))
        index += 1
    return plan


# (patrones, categoría raíz, subcategoría) — todas match_type='contains', owner_id NULL
SYSTEM_RULES: list[tuple[list[str], str, str]] = [
    (["MERCADONA", "CARREFOUR", "LIDL", "DIA", "ALCAMPO", "EROSKI", "CONSUM"],
     "Alimentación", "Supermercado"),
    (["REPSOL", "CEPSA", "GALP", "BP", "SHELL"], "Transporte", "Combustible"),
    (["NETFLIX", "SPOTIFY", "HBO", "DISNEY", "AMAZON PRIME", "FILMIN"], "Ocio", "Suscripciones"),
    (["EMT", "METRO", "RENFE", "CERCANIAS"], "Transporte", "Transporte público"),
    (["FARMACIA"], "Salud", "Farmacia"),
    (["GLOVO", "UBER EATS", "JUST EAT", "DELIVEROO"], "Restauración", "Comida a domicilio"),
]
