import os
from collections.abc import Generator
from datetime import date
from pathlib import Path

from sqlalchemy.engine import make_url

# Aislamiento: antes de importar nada de `app` (que lee la configuración una
# sola vez), los tests pasan a su propia base `<nombre>_test` y sin SMTP, para
# no tocar los datos de desarrollo ni enviar correo.
_dev_url = make_url(os.environ["DATABASE_URL"])
if not (_dev_url.database or "").endswith("_test"):
    _dev_url = _dev_url.set(database=f"{_dev_url.database}_test")
os.environ["DATABASE_URL"] = _dev_url.render_as_string(hide_password=False)
os.environ["SMTP_HOST"] = ""

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine, event, text  # noqa: E402
from sqlalchemy.orm import Session, sessionmaker  # noqa: E402

import app.services.storage as storage  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from app.auth.security import create_access_token, hash_password  # noqa: E402
from app.core.database import engine, get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.account import Account  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.storage import LocalStorageBackend  # noqa: E402

TestingSessionLocal = sessionmaker(bind=engine)

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


@pytest.fixture(scope="session", autouse=True)
def test_database() -> None:
    """Recrea la base de tests desde cero y la migra a la última revisión.

    Así cada ejecución parte de un estado conocido y, de paso, vuelve a
    comprobar que las migraciones funcionan en una base vacía."""
    name = _dev_url.database
    engine.dispose()
    admin = create_engine(_dev_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)'))
        conn.execute(text(f'CREATE DATABASE "{name}"'))
    admin.dispose()

    config = Config(str(ALEMBIC_INI))
    config.set_main_option("script_location", str(ALEMBIC_INI.parent / "alembic"))
    command.upgrade(config, "head")


@pytest.fixture(autouse=True)
def isolated_storage_backend(tmp_path) -> Generator[None, None, None]:
    """Los adjuntos de los tests van a un directorio temporal, no al
    storage real de desarrollo (los rollbacks de `db_session` no deshacen
    escrituras a disco)."""
    original_backend = storage._backend
    storage._backend = LocalStorageBackend(str(tmp_path / "attachments"))
    yield
    storage._backend = original_backend


@pytest.fixture
def db_session() -> Generator[Session, None, None]:
    connection = engine.connect()
    outer_transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    session.begin_nested()

    @event.listens_for(session, "after_transaction_end")
    def _restart_savepoint(sess: Session, trans: object) -> None:
        if trans.nested and not trans._parent.nested:  # type: ignore[attr-defined]
            sess.begin_nested()

    yield session

    session.close()
    outer_transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
def make_user(db_session: Session):
    counter = {"n": 0}

    def _make(email: str | None = None, password: str = "secret123") -> User:
        counter["n"] += 1
        user = User(
            email=email or f"user{counter['n']}@example.com",
            hashed_password=hash_password(password),
        )
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture
def auth_headers(make_user):
    def _headers(user: User | None = None) -> tuple[dict[str, str], User]:
        user = user or make_user()
        token = create_access_token(subject=str(user.id))
        return {"Authorization": f"Bearer {token}"}, user

    return _headers


@pytest.fixture
def make_account(db_session: Session):
    def _make(owner: User, name: str = "Efectivo", type: str = "cash") -> Account:
        account = Account(owner_id=owner.id, name=name, type=type, currency="EUR")
        db_session.add(account)
        db_session.commit()
        db_session.refresh(account)
        return account

    return _make


@pytest.fixture
def set_today(monkeypatch):
    """Fija el "hoy" de los presupuestos (mes en curso, meses pasados de solo
    lectura, ritmo). Se puede llamar varias veces en un mismo test para
    avanzar el reloj."""
    import app.services.budget_calculator as budget_calculator

    def _set(value: date) -> None:
        monkeypatch.setattr(budget_calculator, "today", lambda: value)

    return _set
