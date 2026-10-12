"""Datos inválidos: 422/415 en vez de 500 (revisión técnica del 2026-10-11)."""

from urllib.parse import quote

from fastapi.testclient import TestClient
from sqlalchemy.exc import DataError

from app.main import app
from app.services.file_signature import detect_mime, safe_filename

PNG = b"\x89PNG\r\n\x1a\n contenido"


def _expense(account_id: int, **overrides: object) -> dict[str, object]:
    return {
        "account_id": account_id,
        "amount": "-10.00",
        "direction": "expense",
        "posted_at": "2026-03-01",
        **overrides,
    }


def _field_errors(response) -> set[str]:
    return {error["loc"][-1] for error in response.json()["detail"]}


# --- Límites de los schemas ---------------------------------------------------


def test_counterparty_longer_than_its_column_is_422(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = client.post(
        "/api/v1/transactions/",
        json=_expense(account.id, counterparty="x" * 300),
        headers=headers,
    )

    assert response.status_code == 422
    assert _field_errors(response) == {"counterparty"}


def test_huge_amount_is_422(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = client.post(
        "/api/v1/transactions/",
        json=_expense(account.id, amount="-1000000000000000"),
        headers=headers,
    )

    assert response.status_code == 422
    assert _field_errors(response) == {"amount"}


def test_largest_amount_that_fits_is_accepted(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = client.post(
        "/api/v1/transactions/",
        json=_expense(account.id, amount="-999999999999.99"),
        headers=headers,
    )

    assert response.status_code == 201


def test_goal_name_longer_than_its_column_is_422(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.post(
        "/api/v1/goals/",
        json={"name": "m" * 1000, "target_amount": "100.00"},
        headers=headers,
    )

    assert response.status_code == 422
    assert _field_errors(response) == {"name"}


def test_database_data_error_is_answered_with_422(client: TestClient) -> None:
    def broken() -> None:
        raise DataError("INSERT …", {}, Exception("value too long for type character varying"))

    app.add_api_route("/__test_data_error", broken, methods=["GET"])
    try:
        response = client.get("/__test_data_error")
    finally:
        app.router.routes = [r for r in app.router.routes if r.path != "/__test_data_error"]

    assert response.status_code == 422
    assert "no son válidos" in response.json()["detail"]


# --- Registro -----------------------------------------------------------------


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/api/v1/auth/register", json={"email": "corta@example.com", "password": "1234567"}
    )

    assert response.status_code == 422
    assert _field_errors(response) == {"password"}


def test_register_normalizes_email_and_detects_case_duplicates(client: TestClient) -> None:
    first = client.post(
        "/api/v1/auth/register", json={"email": "Ana@Example.com ", "password": "secreto123"}
    )
    assert first.status_code == 201
    assert first.json()["email"] == "ana@example.com"

    duplicate = client.post(
        "/api/v1/auth/register", json={"email": "ANA@example.com", "password": "secreto123"}
    )
    assert duplicate.status_code == 409


def test_login_ignores_email_case(client: TestClient) -> None:
    client.post(
        "/api/v1/auth/register", json={"email": "luis@example.com", "password": "secreto123"}
    )

    response = client.post(
        "/api/v1/auth/login", data={"username": " Luis@Example.com", "password": "secreto123"}
    )

    assert response.status_code == 200


# --- Adjuntos y avatar ----------------------------------------------------------


def _transaction_id(client: TestClient, headers: dict[str, str], account_id: int) -> int:
    response = client.post("/api/v1/transactions/", json=_expense(account_id), headers=headers)
    return int(response.json()["id"])


def test_unicode_attachment_name_downloads(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    transaction_id = _transaction_id(client, headers, make_account(user).id)
    upload = client.post(
        f"/api/v1/transactions/{transaction_id}/attachments",
        files={"file": ("recibo_日本.png", PNG, "image/png")},
        headers=headers,
    )
    assert upload.status_code == 201

    download = client.get(f"/api/v1/attachments/{upload.json()['id']}", headers=headers)

    assert download.status_code == 200
    assert f"filename*=UTF-8''{quote('recibo_日本.png')}" in download.headers["content-disposition"]
    assert download.headers["x-content-type-options"] == "nosniff"


def test_attachment_name_cannot_inject_into_header(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    transaction_id = _transaction_id(client, headers, make_account(user).id)
    upload = client.post(
        f"/api/v1/transactions/{transaction_id}/attachments",
        files={"file": ('a"; filename="otro.exe.png', PNG, "image/png")},
        headers=headers,
    )

    download = client.get(f"/api/v1/attachments/{upload.json()['id']}", headers=headers)

    disposition = download.headers["content-disposition"]
    assert disposition.count('"') == 2  # solo las comillas de filename="…"


def test_attachment_with_fake_type_is_415(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    transaction_id = _transaction_id(client, headers, make_account(user).id)

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/attachments",
        files={"file": ("recibo.png", b"<script>alert(1)</script>", "image/png")},
        headers=headers,
    )

    assert response.status_code == 415
    listing = client.get(f"/api/v1/transactions/{transaction_id}/attachments", headers=headers)
    assert listing.json() == []


def test_long_attachment_name_is_shortened_keeping_extension(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    transaction_id = _transaction_id(client, headers, make_account(user).id)

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/attachments",
        files={"file": ("f" * 300 + ".pdf", b"%PDF-1.7 contenido", "application/pdf")},
        headers=headers,
    )

    assert response.status_code == 201
    filename = response.json()["filename"]
    assert len(filename) == 255
    assert filename.endswith(".pdf")


def test_avatar_with_fake_type_is_415(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.post(
        "/api/v1/users/me/avatar",
        files={"file": ("avatar.jpg", b"no soy una imagen", "image/jpeg")},
        headers=headers,
    )

    assert response.status_code == 415


def test_detect_mime_recognizes_allowed_types() -> None:
    assert detect_mime(b"\xff\xd8\xff\xe0 jpeg") == "image/jpeg"
    assert detect_mime(PNG) == "image/png"
    assert detect_mime(b"RIFF\x00\x00\x00\x00WEBPVP8 ") == "image/webp"
    assert detect_mime(b"%PDF-1.4") == "application/pdf"
    assert detect_mime(b"<html>") is None


def test_safe_filename_strips_paths() -> None:
    assert safe_filename("C:\\Users\\ana\\recibo.png") == "recibo.png"
    assert safe_filename("") == "adjunto"
