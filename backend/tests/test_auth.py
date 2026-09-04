from fastapi.testclient import TestClient


def test_register_login_me(client: TestClient) -> None:
    register = client.post(
        "/api/v1/auth/register", json={"email": "ana@example.com", "password": "secret123"}
    )
    assert register.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "ana@example.com", "password": "secret123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "ana@example.com"


def test_token_subject_is_user_id_not_email(client: TestClient) -> None:
    from jose import jwt

    from app.core.config import get_settings

    client.post("/api/v1/auth/register", json={"email": "bob@example.com", "password": "secret123"})
    login = client.post(
        "/api/v1/auth/login", data={"username": "bob@example.com", "password": "secret123"}
    )
    token = login.json()["access_token"]
    settings = get_settings()
    payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
    assert payload["sub"].isdigit()
