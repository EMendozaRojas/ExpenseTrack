from fastapi.testclient import TestClient


def test_create_expense(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-15.50",
            "direction": "expense",
            "posted_at": "2026-09-01",
            "note": "Café",
        },
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == "-15.50"
    assert body["direction"] == "expense"
    assert body["source"] == "manual"


def test_amount_sign_must_match_direction(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "15.50",
            "direction": "expense",
            "posted_at": "2026-09-01",
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_zero_amount_rejected(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "0",
            "direction": "expense",
            "posted_at": "2026-09-01",
        },
        headers=headers,
    )
    assert response.status_code == 422


def test_category_must_be_accessible(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-5.00",
            "direction": "expense",
            "posted_at": "2026-09-01",
            "category_id": 999999,
        },
        headers=headers,
    )
    assert response.status_code == 404


def test_account_must_belong_to_user(client: TestClient, auth_headers, make_account) -> None:
    headers_a, _ = auth_headers()
    _, user_b = auth_headers()
    account_b = make_account(user_b)

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account_b.id,
            "amount": "-5.00",
            "direction": "expense",
            "posted_at": "2026-09-01",
        },
        headers=headers_a,
    )
    assert response.status_code == 404


def test_edit_keeps_identity(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    created = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-15.50",
            "direction": "expense",
            "posted_at": "2026-09-01",
        },
        headers=headers,
    ).json()

    updated = client.patch(
        f"/api/v1/transactions/{created['id']}",
        json={"amount": "-20.00", "direction": "expense", "posted_at": "2026-09-02"},
        headers=headers,
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["id"] == created["id"]
    assert body["amount"] == "-20.00"


def test_edit_invalid_amount_rejected(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    created = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-15.50",
            "direction": "expense",
            "posted_at": "2026-09-01",
        },
        headers=headers,
    ).json()

    updated = client.patch(
        f"/api/v1/transactions/{created['id']}",
        json={"amount": "0", "direction": "expense", "posted_at": "2026-09-02"},
        headers=headers,
    )
    assert updated.status_code == 422


def test_cannot_edit_or_delete_other_users_transaction(
    client: TestClient, auth_headers, make_account
) -> None:
    headers_a, user_a = auth_headers()
    headers_b, _ = auth_headers()
    account_a = make_account(user_a)
    created = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account_a.id,
            "amount": "-15.50",
            "direction": "expense",
            "posted_at": "2026-09-01",
        },
        headers=headers_a,
    ).json()

    edit = client.patch(
        f"/api/v1/transactions/{created['id']}",
        json={"amount": "-1.00", "direction": "expense", "posted_at": "2026-09-01"},
        headers=headers_b,
    )
    assert edit.status_code == 404

    delete = client.delete(f"/api/v1/transactions/{created['id']}", headers=headers_b)
    assert delete.status_code == 404


def test_delete_is_soft_and_excluded_from_listing(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    created = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-15.50",
            "direction": "expense",
            "posted_at": "2026-09-01",
        },
        headers=headers,
    ).json()

    delete = client.delete(f"/api/v1/transactions/{created['id']}", headers=headers)
    assert delete.status_code == 204

    listed = client.get("/api/v1/transactions/", headers=headers)
    assert listed.json()["items"] == []


def test_filter_by_account_and_date_range(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    for day in ("2026-08-15", "2026-09-01", "2026-09-15"):
        client.post(
            "/api/v1/transactions/",
            json={
                "account_id": account.id,
                "amount": "-1.00",
                "direction": "expense",
                "posted_at": day,
            },
            headers=headers,
        )

    response = client.get(
        "/api/v1/transactions/",
        params={"account_id": account.id, "date_from": "2026-09-01", "date_to": "2026-09-30"},
        headers=headers,
    )
    items = response.json()["items"]
    assert len(items) == 2
    assert items[0]["posted_at"] == "2026-09-15"


def test_pagination_cursor(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    for day in range(1, 6):
        client.post(
            "/api/v1/transactions/",
            json={
                "account_id": account.id,
                "amount": "-1.00",
                "direction": "expense",
                "posted_at": f"2026-09-0{day}",
            },
            headers=headers,
        )

    first_page = client.get(
        "/api/v1/transactions/", params={"limit": 2}, headers=headers
    ).json()
    assert len(first_page["items"]) == 2
    assert first_page["next_cursor"] is not None

    second_page = client.get(
        "/api/v1/transactions/",
        params={"limit": 2, "cursor": first_page["next_cursor"]},
        headers=headers,
    ).json()
    assert len(second_page["items"]) == 2
    first_ids = {item["id"] for item in first_page["items"]}
    second_ids = {item["id"] for item in second_page["items"]}
    assert first_ids.isdisjoint(second_ids)


def test_create_transfer(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account_a = make_account(user, name="Efectivo", type="cash")
    account_b = make_account(user, name="Ahorro", type="savings")

    response = client.post(
        "/api/v1/transactions/transfer",
        json={
            "from_account_id": account_a.id,
            "to_account_id": account_b.id,
            "amount": "50.00",
            "posted_at": "2026-09-01",
        },
        headers=headers,
    )
    assert response.status_code == 201
    legs = response.json()
    amounts = sorted(leg["amount"] for leg in legs)
    assert amounts == ["-50.00", "50.00"]
    assert legs[0]["transfer_group_id"] == legs[1]["transfer_group_id"]

    balance_a = client.get(f"/api/v1/accounts/{account_a.id}/balance", headers=headers).json()
    balance_b = client.get(f"/api/v1/accounts/{account_b.id}/balance", headers=headers).json()
    assert balance_a["balance"] == "-50.00"
    assert balance_b["balance"] == "50.00"


def test_transfer_requires_both_accounts_owned(
    client: TestClient, auth_headers, make_account
) -> None:
    headers_a, user_a = auth_headers()
    _, user_b = auth_headers()
    account_a = make_account(user_a)
    account_b = make_account(user_b)

    response = client.post(
        "/api/v1/transactions/transfer",
        json={
            "from_account_id": account_a.id,
            "to_account_id": account_b.id,
            "amount": "10.00",
            "posted_at": "2026-09-01",
        },
        headers=headers_a,
    )
    assert response.status_code == 404


def test_deleting_one_leg_deletes_both(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account_a = make_account(user, name="Efectivo", type="cash")
    account_b = make_account(user, name="Ahorro", type="savings")
    legs = client.post(
        "/api/v1/transactions/transfer",
        json={
            "from_account_id": account_a.id,
            "to_account_id": account_b.id,
            "amount": "50.00",
            "posted_at": "2026-09-01",
        },
        headers=headers,
    ).json()

    delete = client.delete(f"/api/v1/transactions/{legs[0]['id']}", headers=headers)
    assert delete.status_code == 204

    listed = client.get("/api/v1/transactions/", headers=headers).json()["items"]
    assert listed == []

    balance_a = client.get(f"/api/v1/accounts/{account_a.id}/balance", headers=headers).json()
    balance_b = client.get(f"/api/v1/accounts/{account_b.id}/balance", headers=headers).json()
    assert balance_a["balance"] == "0.00" or balance_a["balance"] == "0"
    assert balance_b["balance"] == "0.00" or balance_b["balance"] == "0"
