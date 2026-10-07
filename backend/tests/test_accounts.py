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


def test_create_account_as_primary(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    created = client.post(
        "/api/v1/accounts/",
        json={"name": "Efectivo", "type": "cash", "is_primary": True},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.json()["is_primary"] is True


def test_only_one_primary_account_at_a_time(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    first = client.post(
        "/api/v1/accounts/",
        json={"name": "Efectivo", "type": "cash", "is_primary": True},
        headers=headers,
    ).json()
    second = client.post(
        "/api/v1/accounts/",
        json={"name": "Banco", "type": "checking", "is_primary": True},
        headers=headers,
    ).json()

    accounts = client.get("/api/v1/accounts/", headers=headers).json()
    primary_ids = [a["id"] for a in accounts if a["is_primary"]]
    assert primary_ids == [second["id"]]

    # marcar la primera de nuevo como principal quita la marca de la segunda
    client.patch(f"/api/v1/accounts/{first['id']}", json={"is_primary": True}, headers=headers)
    accounts_after = client.get("/api/v1/accounts/", headers=headers).json()
    primary_ids_after = [a["id"] for a in accounts_after if a["is_primary"]]
    assert primary_ids_after == [first["id"]]


def test_create_account_without_type_defaults_to_general(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.post("/api/v1/accounts/", json={"name": "Mi cuenta"}, headers=headers)

    assert response.status_code == 201
    assert response.json()["type"] == "general"
