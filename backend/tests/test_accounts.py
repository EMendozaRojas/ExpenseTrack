from fastapi.testclient import TestClient


def test_create_and_list_account(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.post(
        "/api/v1/accounts/",
        json={
            "name": "Cuenta Nómina",
            "type": "checking",
            "currency": "eur",
            "initial_balance": "100.00",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Cuenta Nómina"
    assert body["currency"] == "EUR"
    assert body["balance"] == "100.00"

    listed = client.get("/api/v1/accounts/", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_account_isolation(client: TestClient, auth_headers, make_account) -> None:
    headers_a, user_a = auth_headers()
    _, user_b = auth_headers()
    account = make_account(user_b)

    response = client.get(f"/api/v1/accounts/{account.id}/balance", headers=headers_a)
    assert response.status_code == 404


def test_balance_reflects_transactions(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-20.00",
            "direction": "expense",
            "posted_at": "2026-09-01",
        },
        headers=headers,
    )

    response = client.get(f"/api/v1/accounts/{account.id}/balance", headers=headers)
    assert response.status_code == 200
    assert response.json()["balance"] == "-20.00"


def test_archive_account_with_movements(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "10.00",
            "direction": "income",
            "posted_at": "2026-09-01",
        },
        headers=headers,
    )

    archived = client.post(f"/api/v1/accounts/{account.id}/archive", headers=headers)
    assert archived.status_code == 200
    assert archived.json()["is_archived"] is True

    listed = client.get("/api/v1/accounts/", headers=headers)
    assert listed.json() == []
