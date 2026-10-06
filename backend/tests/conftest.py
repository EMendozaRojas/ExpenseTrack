from collections.abc import Generator
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session, sessionmaker

import app.services.storage as storage
from app.auth.security import create_access_token, hash_password
from app.core.database import engine, get_db
from app.main import app
from app.models.account import Account
from app.models.user import User
from app.services.storage import LocalStorageBackend

TestingSessionLocal = sessionmaker(bind=engine)


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
