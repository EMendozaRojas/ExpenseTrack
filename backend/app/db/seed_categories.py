"""Seed de categorías y reglas de sistema.

Taxonomía de gasto v2 (confirmada en sesión de producto): 10 categorías
principales x subcategorías, 2 niveles fijos. `is_fixed` se define por
subcategoría; las transacciones siempre se asignan a una subcategoría, nunca
a la categoría principal directamente — por eso las raíces no llevan
`is_fixed` significativo (se guardan como False).

Reemplaza la taxonomía anterior (ver migración
`fac793ec36d3_hierarchical_categories_and_rules` para el seed original y
`taxonomy_v2_fixed_flag` para la migración de datos que reescribe esto).
"""

from dataclasses import dataclass, field

_PALETTE = [
    "#4F86C6", "#E4572E", "#76B041", "#F3A712", "#8E7CC3",
    "#48A9A6", "#D64550", "#3E92CC", "#6A994E", "#B56576",
    "#457B9D", "#E07A5F",
]


@dataclass(frozen=True)
class SeedSub:
    name: str
    is_fixed: bool = False


@dataclass(frozen=True)
class SeedRoot:
    name: str
    icon: str
    subcategories: list[SeedSub] = field(default_factory=list)


# Nombre exacto de la subcategoría por defecto para movimientos sin regla que
# les aplique. Es una categoría de sistema real (is_system=true), no un
# category_id NULL — toda transacción de income/expense debe llevar una.
UNCATEGORIZED_EXPENSE = ("Finanzas y Otros", "Sin Clasificar")
UNCATEGORIZED_INCOME = ("Otros ingresos", "Sin clasificar")

EXPENSE_ROOTS: list[SeedRoot] = [
    SeedRoot("Alimentación", "🛒", [
        SeedSub("Supermercado"),
    ]),
    SeedRoot("Restauración", "🍽️", [
        SeedSub("Restaurantes"), SeedSub("Cafeterías"), SeedSub("Delivery"), SeedSub("Bares/Copas"),
    ]),
    SeedRoot("Vivienda", "🏠", [
        SeedSub("Alquiler/Hipoteca", is_fixed=True),
        SeedSub("Suministros (Luz/Agua/Gas)", is_fixed=True),
        SeedSub("Internet/Móvil", is_fixed=True),
        SeedSub("Mantenimiento"),
    ]),
    SeedRoot("Transporte", "🚌", [
        SeedSub("Combustible"), SeedSub("Transporte Público"), SeedSub("Taxi/VTC"),
        SeedSub("Mantenimiento/Parking"),
    ]),
    SeedRoot("Compras y Personal", "🛍️", [
        SeedSub("Ropa y Calzado"), SeedSub("Tecnología"), SeedSub("Hogar"), SeedSub("Cuidado Personal"),
    ]),
    SeedRoot("Suscripciones", "🔁", [
        SeedSub("Streaming", is_fixed=True),
        SeedSub("Software", is_fixed=True),
        SeedSub("Gimnasio", is_fixed=True),
        SeedSub("Servicios Recurrentes", is_fixed=True),
    ]),
    SeedRoot("Ocio", "🎬", [
        SeedSub("Cine/Eventos"), SeedSub("Viajes/Hoteles"), SeedSub("Juegos/Aficiones"),
    ]),
    SeedRoot("Salud", "💊", [
        SeedSub("Farmacia"), SeedSub("Médicos/Dentista"),
    ]),
    SeedRoot("Familia y Mascotas", "👨‍👩‍👧", [
        SeedSub("Educación", is_fixed=True),
        SeedSub("Mascotas"),
        SeedSub("Guardería/Colegio", is_fixed=True),
    ]),
    SeedRoot("Finanzas y Otros", "🏦", [
        SeedSub("Comisiones", is_fixed=True),
        SeedSub("Impuestos", is_fixed=True),
        SeedSub("Sin Clasificar"),
    ]),
]

INCOME_ROOTS: list[SeedRoot] = [
    SeedRoot("Nómina y salario", "💼", [
        SeedSub("Nómina"), SeedSub("Pagas extra"), SeedSub("Bonus"),
    ]),
    SeedRoot("Trabajo autónomo", "🧾", [SeedSub("Facturas a clientes")]),
    SeedRoot("Rendimientos", "📈", [
        SeedSub("Intereses"), SeedSub("Dividendos"), SeedSub("Alquileres cobrados"),
    ]),
    SeedRoot("Reembolsos", "↩️", [
        SeedSub("Devoluciones de compras"), SeedSub("Devolución de Hacienda"),
        SeedSub("Gastos compartidos"),
    ]),
    SeedRoot("Ayudas y prestaciones", "🤝", [SeedSub("Subvenciones"), SeedSub("Prestaciones")]),
    SeedRoot("Otros ingresos", "💰", [SeedSub("Regalos recibidos"), SeedSub("Sin clasificar")]),
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
    (["NETFLIX", "SPOTIFY", "HBO", "DISNEY", "AMAZON PRIME", "FILMIN"], "Suscripciones", "Streaming"),
    (["EMT", "METRO", "RENFE", "CERCANIAS"], "Transporte", "Transporte Público"),
    (["FARMACIA"], "Salud", "Farmacia"),
    (["GLOVO", "UBER EATS", "JUST EAT", "DELIVEROO"], "Restauración", "Delivery"),
]

# Mapa best-effort de la taxonomía anterior (Apéndice A original) a la v2,
# usado solo por la data-migration para reubicar transacciones y reglas de
# usuario existentes. Ambigua -> UNCATEGORIZED.
LEGACY_SUBCATEGORY_MAP: dict[str, tuple[str, str]] = {
    "Supermercado": ("Alimentación", "Supermercado"),
    "Restaurantes": ("Restauración", "Restaurantes"),
    "Comida a domicilio": ("Restauración", "Delivery"),
    "Alquiler / Hipoteca": ("Vivienda", "Alquiler/Hipoteca"),
    "Suministros (luz, agua, gas)": ("Vivienda", "Suministros (Luz/Agua/Gas)"),
    "Internet y teléfono": ("Vivienda", "Internet/Móvil"),
    "Mantenimiento y reparaciones": ("Vivienda", "Mantenimiento"),
    "Seguro de hogar": ("Suscripciones", "Servicios Recurrentes"),
    "Transporte público": ("Transporte", "Transporte Público"),
    "Combustible": ("Transporte", "Combustible"),
    "Parking y peajes": ("Transporte", "Mantenimiento/Parking"),
    "Taxi / VTC": ("Transporte", "Taxi/VTC"),
    "Mantenimiento del vehículo": ("Transporte", "Mantenimiento/Parking"),
    "Seguro del coche": ("Suscripciones", "Servicios Recurrentes"),
    "Impuestos e ITV": ("Finanzas y Otros", "Impuestos"),
    "Farmacia": ("Salud", "Farmacia"),
    "Médico y dentista": ("Salud", "Médicos/Dentista"),
    "Seguro médico": ("Suscripciones", "Servicios Recurrentes"),
    "Gimnasio y deporte": ("Suscripciones", "Gimnasio"),
    "Cine, teatro y eventos": ("Ocio", "Cine/Eventos"),
    "Libros, música y juegos": ("Ocio", "Juegos/Aficiones"),
    "Suscripciones": ("Suscripciones", "Streaming"),
    "Viajes y vacaciones": ("Ocio", "Viajes/Hoteles"),
    "Aficiones": ("Ocio", "Juegos/Aficiones"),
    "Ropa y calzado": ("Compras y Personal", "Ropa y Calzado"),
    "Electrónica": ("Compras y Personal", "Tecnología"),
    "Hogar y decoración": ("Compras y Personal", "Hogar"),
    "Cuidado personal": ("Compras y Personal", "Cuidado Personal"),
    "Matrículas y cursos": ("Familia y Mascotas", "Educación"),
    "Material y libros": ("Familia y Mascotas", "Educación"),
    "Idiomas": ("Familia y Mascotas", "Educación"),
    "Comisiones bancarias": ("Finanzas y Otros", "Comisiones"),
    "Impuestos y tasas": ("Finanzas y Otros", "Impuestos"),
    "Comida y accesorios": ("Familia y Mascotas", "Mascotas"),
    "Veterinario": ("Familia y Mascotas", "Mascotas"),
    "Guardería y colegio": ("Familia y Mascotas", "Guardería/Colegio"),
}
