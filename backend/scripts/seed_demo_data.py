"""Datos de prueba realistas para probar la interfaz manualmente.

Genera, para un usuario demo fijo, los últimos 3 meses calendario completos
de movimientos (30-40 por mes, EUR, usando la taxonomía oficial de 2
niveles) y 3 metas de ahorro con distinto avance y aportaciones repartidas
en esos mismos 3 meses (para poder probar /goals/{id}/projection).

Idempotente: se puede re-ejecutar, borra y regenera los datos del usuario
demo sin tocar el resto de la base.

Uso:
    docker compose exec backend python -m scripts.seed_demo_data
"""

import random
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from app.auth.security import hash_password
from app.core.database import SessionLocal
from app.models.account import Account
from app.models.category import Category
from app.models.goal_contribution import GoalContribution
from app.models.savings_goal import SavingsGoal
from app.models.transaction import Transaction
from app.models.user import User

DEMO_EMAIL = "demo.datos@example.com"
DEMO_PASSWORD = "demodatos1234"


def month_bounds(year: int, month: int) -> tuple[date, date]:
    start = date(year, month, 1)
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1
    end = date(next_year, next_month, 1) - timedelta(days=1)
    return start, end


def last_n_full_months(n: int) -> list[tuple[int, int]]:
    """Los `n` meses calendario completos anteriores al actual, más antiguo primero."""
    today = date.today()
    months = []
    year, month = today.year, today.month
    for _ in range(n):
        month -= 1
        if month == 0:
            month, year = 12, year - 1
        months.append((year, month))
    return list(reversed(months))


def random_day(year: int, month: int, min_day: int = 1, max_day: int | None = None) -> date:
    start, end = month_bounds(year, month)
    last_day = max_day or end.day
    return date(year, month, random.randint(min_day, min(last_day, end.day)))


def amount(min_value: float, max_value: float) -> Decimal:
    return Decimal(str(round(random.uniform(min_value, max_value), 2)))


def find_category(db, kind: str, root_name: str, sub_name: str) -> int:
    root = (
        db.query(Category)
        .filter(
            Category.kind == kind,
            Category.name == root_name,
            Category.parent_id.is_(None),
            Category.is_system.is_(True),
        )
        .one()
    )
    sub = db.query(Category).filter(Category.parent_id == root.id, Category.name == sub_name).one()
    return sub.id


def add_transaction(
    db,
    account: Account,
    user: User,
    *,
    signed_amount: Decimal,
    direction: str,
    posted_at: date,
    category_id: int,
    description: str,
) -> None:
    db.add(
        Transaction(
            account_id=account.id,
            owner_id=user.id,
            amount=signed_amount,
            direction=direction,
            posted_at=posted_at,
            category_id=category_id,
            currency=account.currency,
            fx_rate_to_account_currency=None,
            amount_in_account_currency=signed_amount,
            raw_description=description,
            source="manual",
        )
    )


def seed_transactions(db, account: Account, user: User, cat: dict[str, int]) -> int:
    months = last_n_full_months(3)
    total = 0

    for year, month in months:
        # --- ingreso fijo ---
        add_transaction(
            db,
            account,
            user,
            signed_amount=amount(1900, 2150),
            direction="income",
            posted_at=date(year, month, 3),
            category_id=cat["nomina"],
            description="NOMINA EMPRESA SL",
        )
        total += 1

        # --- gastos fijos, uno por mes ---
        fixed = [
            ("alquiler", "ALQUILER PISO C/ MAYOR 14", 750, 750, 1, 1),
            (
                "suministros",
                random.choice(["ENDESA ENERGIA", "IBERDROLA CLIENTES", "NATURGY"]),
                55,
                98,
                3,
                7,
            ),
            ("internet", random.choice(["MOVISTAR FIBRA", "VODAFONE ESPANA"]), 34, 46, 3, 7),
            ("streaming", "NETFLIX.COM", 12.99, 12.99, 1, 1),
            ("streaming", "SPOTIFY PREMIUM", 9.99, 9.99, 1, 1),
            ("gimnasio", "BASIC FIT MADRID", 29.90, 29.90, 1, 1),
            ("transporte_publico", "EMT MADRID ABONO TRANSPORTE", 54.60, 54.60, 1, 3),
            ("comisiones", "COMISION MANTENIMIENTO CUENTA", 2, 6, 5, 5),
        ]
        for cat_key, desc, lo, hi, min_day, max_day in fixed:
            add_transaction(
                db,
                account,
                user,
                signed_amount=-amount(lo, hi),
                direction="expense",
                posted_at=random_day(year, month, min_day, max_day),
                category_id=cat[cat_key],
                description=desc,
            )
            total += 1

        # --- gastos variables, varias ocurrencias por mes ---
        variable = [
            (
                "supermercado",
                ["MERCADONA", "CARREFOUR EXPRESS", "DIA MARKET", "LIDL"],
                12,
                75,
                (6, 8),
            ),
            (
                "restaurantes",
                ["RESTAURANTE LA TASCA", "GRUPO VIPS", "RESTAURANTE EL HORNO"],
                18,
                48,
                (3, 5),
            ),
            (
                "cafeterias",
                ["STARBUCKS", "CAFETERIA CENTRAL", "PANADERIA SAN MIGUEL"],
                1.8,
                4.5,
                (6, 9),
            ),
            ("delivery", ["GLOVO", "UBER EATS", "JUST EAT"], 14, 32, (2, 3)),
            ("combustible", ["REPSOL", "CEPSA", "SHELL"], 45, 70, (2, 2)),
            ("cine", ["CINES YELMO"], 8, 13, (0, 1)),
            ("ropa", ["ZARA", "H&M", "DECATHLON"], 20, 90, (0, 2)),
            ("cuidado_personal", ["PERFUMERIA DOUGLAS", "PELUQUERIA STYLE"], 15, 45, (0, 1)),
            ("farmacia", ["FARMACIA LCDA GARCIA"], 8, 28, (1, 2)),
        ]
        for cat_key, descriptions, lo, hi, (min_n, max_n) in variable:
            occurrences = random.randint(min_n, max_n)
            for _ in range(occurrences):
                add_transaction(
                    db,
                    account,
                    user,
                    signed_amount=-amount(lo, hi),
                    direction="expense",
                    posted_at=random_day(year, month),
                    category_id=cat[cat_key],
                    description=random.choice(descriptions),
                )
                total += 1

    return total


def seed_goals(db, user: User) -> None:
    created_at = datetime.now(UTC) - timedelta(days=110)
    months = last_n_full_months(3)

    goals_plan = [
        ("Fondo de emergencia", Decimal("3000.00"), date(2026, 12, 31), Decimal("300.00")),
        ("Viaje a Japón", Decimal("2000.00"), None, Decimal("400.00")),
        ("Renovar el coche", Decimal("10000.00"), None, Decimal("250.00")),
    ]

    for name, target, target_date, monthly_contribution in goals_plan:
        goal = SavingsGoal(
            owner_id=user.id,
            name=name,
            target_amount=target,
            target_date=target_date,
            status="active",
            created_at=created_at,
        )
        db.add(goal)
        db.flush()

        for year, month in months:
            db.add(
                GoalContribution(
                    goal_id=goal.id,
                    amount=monthly_contribution,
                    contributed_at=date(year, month, 5),
                )
            )


def main() -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == DEMO_EMAIL).first()
        if user is None:
            user = User(email=DEMO_EMAIL, hashed_password=hash_password(DEMO_PASSWORD))
            db.add(user)
            db.flush()

        account = db.query(Account).filter(Account.owner_id == user.id).first()
        if account is None:
            account = Account(
                owner_id=user.id,
                name="Cuenta Principal",
                type="checking",
                currency="EUR",
                initial_balance=Decimal("500.00"),
            )
            db.add(account)
            db.flush()

        cat = {
            "supermercado": find_category(db, "expense", "Alimentación", "Supermercado"),
            "restaurantes": find_category(db, "expense", "Restauración", "Restaurantes"),
            "cafeterias": find_category(db, "expense", "Restauración", "Cafeterías"),
            "delivery": find_category(db, "expense", "Restauración", "Delivery"),
            "alquiler": find_category(db, "expense", "Vivienda", "Alquiler/Hipoteca"),
            "suministros": find_category(db, "expense", "Vivienda", "Suministros (Luz/Agua/Gas)"),
            "internet": find_category(db, "expense", "Vivienda", "Internet/Móvil"),
            "combustible": find_category(db, "expense", "Transporte", "Combustible"),
            "transporte_publico": find_category(db, "expense", "Transporte", "Transporte Público"),
            "streaming": find_category(db, "expense", "Suscripciones", "Streaming"),
            "gimnasio": find_category(db, "expense", "Suscripciones", "Gimnasio"),
            "cine": find_category(db, "expense", "Ocio", "Cine/Eventos"),
            "ropa": find_category(db, "expense", "Compras y Personal", "Ropa y Calzado"),
            "cuidado_personal": find_category(
                db, "expense", "Compras y Personal", "Cuidado Personal"
            ),
            "farmacia": find_category(db, "expense", "Salud", "Farmacia"),
            "comisiones": find_category(db, "expense", "Finanzas y Otros", "Comisiones"),
            "nomina": find_category(db, "income", "Nómina y salario", "Nómina"),
        }

        # idempotente: borra lo generado antes por este script para este usuario
        db.query(GoalContribution).filter(
            GoalContribution.goal_id.in_(
                db.query(SavingsGoal.id).filter(SavingsGoal.owner_id == user.id)
            )
        ).delete(synchronize_session=False)
        db.query(SavingsGoal).filter(SavingsGoal.owner_id == user.id).delete(
            synchronize_session=False
        )
        db.query(Transaction).filter(Transaction.owner_id == user.id).delete(
            synchronize_session=False
        )
        db.commit()

        total_tx = seed_transactions(db, account, user, cat)
        seed_goals(db, user)
        db.commit()

        print(f"Usuario demo: {DEMO_EMAIL} / {DEMO_PASSWORD}")
        print(f"Cuenta: {account.name} ({account.currency})")
        print(f"Transacciones generadas: {total_tx}")
        print("Metas: Fondo de emergencia, Viaje a Japón, Renovar el coche")
    finally:
        db.close()


if __name__ == "__main__":
    main()
