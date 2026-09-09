from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.services import google_oauth


def test_login_issues_access_and_refresh_token(client: TestClient) -> None:
    client.post("/api/v1/auth/register", json={"email": "ana@example.com", "password": "secret123"})

    login = client.post(
        "/api/v1/auth/login", data={"username": "ana@example.com", "password": "secret123"}
    )
    assert login.status_code == 200
    body = login.json()
    assert body["access_token"]
    assert body["refresh_token"]


def test_refresh_rotates_token_and_old_one_stops_working(client: TestClient) -> None:
    client.post("/api/v1/auth/register", json={"email": "ana@example.com", "password": "secret123"})
    login = client.post(
        "/api/v1/auth/login", data={"username": "ana@example.com", "password": "secret123"}
    ).json()

    refreshed = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert new_tokens["refresh_token"] != login["refresh_token"]

    reused_old = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert reused_old.status_code == 401


def test_logout_revokes_refresh_token(client: TestClient) -> None:
    client.post("/api/v1/auth/register", json={"email": "ana@example.com", "password": "secret123"})
    login = client.post(
        "/api/v1/auth/login", data={"username": "ana@example.com", "password": "secret123"}
    ).json()

    logout = client.post("/api/v1/auth/logout", json={"refresh_token": login["refresh_token"]})
    assert logout.status_code == 204

    refreshed = client.post(
        "/api/v1/auth/refresh", json={"refresh_token": login["refresh_token"]}
    )
    assert refreshed.status_code == 401


def test_invalid_refresh_token_rejected(client: TestClient) -> None:
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "no-existe"})
    assert response.status_code == 401


def test_oauth_start_returns_503_without_credentials_configured(client: TestClient) -> None:
    response = client.get("/api/v1/auth/oauth/google/start", follow_redirects=False)
    assert response.status_code == 503


def test_oauth_start_redirects_to_google_when_configured(client: TestClient) -> None:
    from app.core.config import get_settings

    settings = get_settings()
    original_client_id = settings.google_client_id
    settings.google_client_id = "fake-client-id"
    try:
        response = client.get("/api/v1/auth/oauth/google/start", follow_redirects=False)
    finally:
        settings.google_client_id = original_client_id
    assert response.status_code == 307
    assert "accounts.google.com" in response.headers["location"]


def test_oauth_callback_rejects_invalid_state(client: TestClient) -> None:
    response = client.get(
        "/api/v1/auth/oauth/google/callback",
        params={"code": "abc", "state": "not-a-valid-state"},
        follow_redirects=False,
    )
    assert response.status_code == 400


def test_oauth_callback_creates_new_user_and_links_identity(
    client: TestClient, db_session
) -> None:
    from app.models.auth_identity import AuthIdentity
    from app.models.user import User

    state = google_oauth.create_state()
    fake_userinfo = {"sub": "google-uid-123", "email": "nueva@example.com"}

    with patch.object(google_oauth, "exchange_code_for_userinfo", AsyncMock(return_value=fake_userinfo)):
        response = client.get(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "fake-code", "state": state},
            follow_redirects=False,
        )

    assert response.status_code == 307
    location = response.headers["location"]
    assert "/auth/social-callback" in location
    assert "access_token=" in location
    assert "refresh_token=" in location

    user = db_session.query(User).filter(User.email == "nueva@example.com").first()
    assert user is not None
    assert user.hashed_password is None
    identity = db_session.query(AuthIdentity).filter(AuthIdentity.user_id == user.id).first()
    assert identity is not None
    assert identity.provider_uid == "google-uid-123"


def test_oauth_callback_links_existing_account_by_email(client: TestClient, db_session) -> None:
    from app.models.auth_identity import AuthIdentity

    register = client.post(
        "/api/v1/auth/register", json={"email": "existente@example.com", "password": "secret123"}
    )
    existing_user_id = register.json()["id"]

    state = google_oauth.create_state()
    fake_userinfo = {"sub": "google-uid-456", "email": "existente@example.com"}

    with patch.object(google_oauth, "exchange_code_for_userinfo", AsyncMock(return_value=fake_userinfo)):
        response = client.get(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "fake-code", "state": state},
            follow_redirects=False,
        )

    assert response.status_code == 307
    identity = (
        db_session.query(AuthIdentity).filter(AuthIdentity.provider_uid == "google-uid-456").first()
    )
    assert identity is not None
    assert identity.user_id == existing_user_id


def test_oauth_callback_reuses_identity_on_second_login(client: TestClient, db_session) -> None:
    from app.models.user import User

    state1 = google_oauth.create_state()
    fake_userinfo = {"sub": "google-uid-789", "email": "repetida@example.com"}
    with patch.object(google_oauth, "exchange_code_for_userinfo", AsyncMock(return_value=fake_userinfo)):
        client.get(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "fake-code-1", "state": state1},
            follow_redirects=False,
        )

    state2 = google_oauth.create_state()
    with patch.object(google_oauth, "exchange_code_for_userinfo", AsyncMock(return_value=fake_userinfo)):
        client.get(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "fake-code-2", "state": state2},
            follow_redirects=False,
        )

    users = db_session.query(User).filter(User.email == "repetida@example.com").all()
    assert len(users) == 1


def test_password_login_rejected_for_social_only_user(client: TestClient) -> None:
    state = google_oauth.create_state()
    fake_userinfo = {"sub": "google-uid-999", "email": "solosocial@example.com"}
    with patch.object(google_oauth, "exchange_code_for_userinfo", AsyncMock(return_value=fake_userinfo)):
        client.get(
            "/api/v1/auth/oauth/google/callback",
            params={"code": "fake-code", "state": state},
            follow_redirects=False,
        )

    login = client.post(
        "/api/v1/auth/login",
        data={"username": "solosocial@example.com", "password": "cualquiera"},
    )
    assert login.status_code == 401
