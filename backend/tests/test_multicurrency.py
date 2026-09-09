from fastapi.testclient import TestClient


def test_get_preferences_defaults(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.get("/api/v1/users/me/preferences/", headers=headers)
    assert response.status_code == 200
    assert response.json() == {"base_currency": "EUR", "locale": "es-ES"}


def test_update_preferences(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.patch(
        "/api/v1/users/me/preferences/", json={"base_currency": "usd"}, headers=headers
    )
    assert response.status_code == 200
    assert response.json()["base_currency"] == "USD"
    assert response.json()["locale"] == "es-ES"


def test_invalid_currency_code_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.patch(
        "/api/v1/users/me/preferences/", json={"base_currency": "EURO"}, headers=headers
    )
    assert response.status_code == 422


def test_create_and_list_fx_rate(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    created = client.post(
        "/api/v1/fx-rates/",
        json={"rate_date": "2026-03-01", "base": "usd", "quote": "eur", "rate": "0.92"},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["base"] == "USD"

    listed = client.get("/api/v1/fx-rates/", params={"base": "USD"}, headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_duplicate_fx_rate_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    payload = {"rate_date": "2026-03-01", "base": "USD", "quote": "EUR", "rate": "0.92"}

    first = client.post("/api/v1/fx-rates/", json=payload, headers=headers)
    assert first.status_code == 201
    second = client.post("/api/v1/fx-rates/", json=payload, headers=headers)
    assert second.status_code == 409


def test_transaction_same_currency_as_account_needs_no_rate(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-10.00",
            "direction": "expense",
            "posted_at": "2026-03-01",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["currency"] == "EUR"
    assert body["fx_rate_to_account_currency"] is None
    assert body["amount_in_account_currency"] == "-10.00"


def test_transaction_different_currency_without_rate_rejected(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-10.00",
            "direction": "expense",
            "posted_at": "2026-03-01",
            "currency": "USD",
        },
        headers=headers,
    )
    assert response.status_code == 422
    assert "tasa de cambio" in response.json()["detail"]


def test_transaction_different_currency_converted_with_rate(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    client.post(
        "/api/v1/fx-rates/",
        json={"rate_date": "2026-03-01", "base": "USD", "quote": "EUR", "rate": "0.90"},
        headers=headers,
    )

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-100.00",
            "direction": "expense",
            "posted_at": "2026-03-01",
            "currency": "USD",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["currency"] == "USD"
    assert body["fx_rate_to_account_currency"] == "0.900000"
    assert body["amount_in_account_currency"] == "-90.00"


def test_transaction_uses_inverse_rate_when_only_that_direction_exists(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    # solo existe EUR->USD, la conversión USD->EUR debe usar la inversa
    client.post(
        "/api/v1/fx-rates/",
        json={"rate_date": "2026-03-01", "base": "EUR", "quote": "USD", "rate": "1.10"},
        headers=headers,
    )

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-110.00",
            "direction": "expense",
            "posted_at": "2026-03-01",
            "currency": "USD",
        },
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["amount_in_account_currency"] == "-100.00"
