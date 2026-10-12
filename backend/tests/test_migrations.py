"""Instalación limpia: todas las migraciones se aplican sobre una BD vacía.

Vigila que la cadena de Alembic no dependa de código de `app/` que cambie con
el tiempo (pasó con el seed de categorías y nadie lo notó en un mes).
"""

import uuid
from collections.abc import Generator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.exc import ProgrammingError

from app.core.config import get_settings

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


@pytest.fixture
def empty_database_url() -> Generator[URL, None, None]:
    base_url = make_url(get_settings().database_url)
    name = f"{base_url.database}_migrations_{uuid.uuid4().hex[:8]}"
    admin = create_engine(base_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    try:
        with admin.connect() as conn:
            conn.execute(text(f'CREATE DATABASE "{name}"'))
    except ProgrammingError as exc:
        admin.dispose()
        pytest.skip(f"El usuario de Postgres no puede crear bases de datos: {exc}")
    try:
        yield base_url.set(database=name)
    finally:
        with admin.connect() as conn:
            conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        admin.dispose()


def test_all_migrations_apply_on_an_empty_database(empty_database_url: URL) -> None:
    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_INI.parent / "alembic"))
    config.attributes["database_url"] = empty_database_url.render_as_string(hide_password=False)

    command.upgrade(config, "head")

    engine = create_engine(empty_database_url)
    try:
        with engine.connect() as conn:
            head = ScriptDirectory.from_config(config).get_current_head()
            assert conn.execute(text("SELECT version_num FROM alembic_version")).scalar() == head

            tables = set(inspect(conn).get_table_names())
            assert {"users", "accounts", "transactions", "categories", "budgets"} <= tables

            expense_roots = conn.execute(
                text(
                    "SELECT count(*) FROM categories "
                    "WHERE is_system AND kind = 'expense' AND parent_id IS NULL"
                )
            ).scalar()
            assert expense_roots == 10

            uncategorized = conn.execute(
                text(
                    "SELECT count(*) FROM categories c JOIN categories p ON p.id = c.parent_id "
                    "WHERE c.is_system AND p.name = 'Finanzas y Otros' "
                    "AND c.name = 'Sin Clasificar'"
                )
            ).scalar()
            assert uncategorized == 1

            system_rules = conn.execute(
                text("SELECT count(*) FROM categorization_rules WHERE owner_id IS NULL")
            ).scalar()
            assert system_rules == 27
    finally:
        engine.dispose()
