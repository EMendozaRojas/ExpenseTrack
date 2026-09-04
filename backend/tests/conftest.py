from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event
from sqlalchemy.orm import Session, sessionmaker

from app.auth.security import create_access_token, hash_password
from app.core.database import engine, get_db
from app.main import app
from app.models.account import Account
from app.models.user import User

TestingSessionLocal = sessionmaker(bind=engine)


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
