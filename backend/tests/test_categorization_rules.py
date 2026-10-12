from fastapi.testclient import TestClient


def _find_category(
    client: TestClient, headers: dict[str, str], kind: str, root_name: str, sub_name: str
) -> int:
    roots = client.get("/api/v1/categories/", params={"kind": kind}, headers=headers).json()
    root = next(r for r in roots if r["name"] == root_name)
    sub = next(c for c in root["children"] if c["name"] == sub_name)
    return sub["id"]


def test_create_rule(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    response = client.post(
        "/api/v1/categorization-rules/",
        json={"match_type": "contains", "pattern": "MERCADONA", "category_id": category_id},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["is_enabled"] is True


def test_rule_target_must_be_visible(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.post(
        "/api/v1/categorization-rules/",
        json={"match_type": "contains", "pattern": "X", "category_id": 999999},
        headers=headers,
    )
    assert response.status_code == 404


def test_list_update_and_delete_rule(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    other_category_id = _find_category(client, headers, "expense", "Ocio", "Juegos/Aficiones")

    created = client.post(
        "/api/v1/categorization-rules/",
        json={"match_type": "contains", "pattern": "DIA", "category_id": category_id},
        headers=headers,
    ).json()

    listed = client.get("/api/v1/categorization-rules/", headers=headers)
    assert listed.status_code == 200
    assert any(rule["id"] == created["id"] for rule in listed.json())

    updated = client.patch(
        f"/api/v1/categorization-rules/{created['id']}",
        json={"category_id": other_category_id, "is_enabled": False, "priority": 5},
        headers=headers,
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["category_id"] == other_category_id
    assert body["is_enabled"] is False
    assert body["priority"] == 5

    deleted = client.delete(f"/api/v1/categorization-rules/{created['id']}", headers=headers)
    assert deleted.status_code == 204

    listed_after = client.get("/api/v1/categorization-rules/", headers=headers).json()
    assert all(rule["id"] != created["id"] for rule in listed_after)


def test_update_rejects_unsupported_match_type_and_foreign_category(
    client: TestClient, auth_headers
) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    created = client.post(
        "/api/v1/categorization-rules/",
        json={"match_type": "contains", "pattern": "DIA", "category_id": category_id},
        headers=headers,
    ).json()

    bad_match_type = client.patch(
        f"/api/v1/categorization-rules/{created['id']}",
        json={"match_type": "regex"},
        headers=headers,
    )
    assert bad_match_type.status_code == 422

    bad_category = client.patch(
        f"/api/v1/categorization-rules/{created['id']}",
        json={"category_id": 999999},
        headers=headers,
    )
    assert bad_category.status_code == 404


def test_cannot_update_or_delete_other_users_rule(client: TestClient, auth_headers) -> None:
    headers_a, _ = auth_headers()
    headers_b, _ = auth_headers()
    category_id = _find_category(client, headers_a, "expense", "Alimentación", "Supermercado")
    created = client.post(
        "/api/v1/categorization-rules/",
        json={"match_type": "contains", "pattern": "DIA", "category_id": category_id},
        headers=headers_a,
    ).json()

    update = client.patch(
        f"/api/v1/categorization-rules/{created['id']}",
        json={"priority": 9},
        headers=headers_b,
    )
    assert update.status_code == 404

    delete = client.delete(f"/api/v1/categorization-rules/{created['id']}", headers=headers_b)
    assert delete.status_code == 404


def test_preview_rejects_unsupported_match_type(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.get(
        "/api/v1/categorization-rules/preview",
        params={"pattern": "X", "match_type": "regex"},
        headers=headers,
    )
    assert response.status_code == 422


def test_apply_unknown_rule_returns_404(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.post("/api/v1/categorization-rules/999999/apply", headers=headers)
    assert response.status_code == 404


def test_unsupported_match_type_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    response = client.post(
        "/api/v1/categorization-rules/",
        json={"match_type": "regex", "pattern": "X", "category_id": category_id},
        headers=headers,
    )
    assert response.status_code == 422


def test_transaction_auto_categorized_by_system_rule(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-30.00",
            "direction": "expense",
            "posted_at": "2026-09-01",
            "note": "COMPRA EN MERCADONA 1234",
        },
        headers=headers,
    )
    assert response.json()["category_id"] == supermercado_id


def test_no_rule_matches_leaves_uncategorized(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    sin_clasificar_id = _find_category(
        client, headers, "expense", "Finanzas y Otros", "Sin Clasificar"
    )

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-30.00",
            "direction": "expense",
            "posted_at": "2026-09-01",
            "note": "ALGO DESCONOCIDO",
        },
        headers=headers,
    )
    assert response.json()["category_id"] == sin_clasificar_id

    listed = client.get("/api/v1/transactions/", params={"category_id": ""}, headers=headers)
    assert listed.status_code in (200, 422)


def test_manual_category_never_overridden_by_rules(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    ocio_id = _find_category(client, headers, "expense", "Ocio", "Juegos/Aficiones")

    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-30.00",
            "direction": "expense",
            "posted_at": "2026-09-01",
            "note": "COMPRA EN MERCADONA 1234",
            "category_id": ocio_id,
        },
        headers=headers,
    )
    assert response.json()["category_id"] == ocio_id


def test_preview_and_apply_fill_blanks_only(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    ocio_id = _find_category(client, headers, "expense", "Ocio", "Juegos/Aficiones")
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    already_categorized = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-5.00",
            "direction": "expense",
            "posted_at": "2026-09-01",
            "note": "TIENDA XYZ",
            "category_id": ocio_id,
        },
        headers=headers,
    ).json()
    uncategorized = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-8.00",
            "direction": "expense",
            "posted_at": "2026-09-02",
            "note": "TIENDA XYZ",
        },
        headers=headers,
    ).json()

    rule = client.post(
        "/api/v1/categorization-rules/",
        json={"match_type": "contains", "pattern": "TIENDA XYZ", "category_id": supermercado_id},
        headers=headers,
    ).json()

    preview = client.get(
        "/api/v1/categorization-rules/preview",
        params={"pattern": "TIENDA XYZ", "match_type": "contains"},
        headers=headers,
    )
    assert preview.json()["matching_count"] == 2

    apply = client.post(f"/api/v1/categorization-rules/{rule['id']}/apply", headers=headers)
    assert apply.json()["updated_count"] == 1

    items = client.get("/api/v1/transactions/", headers=headers).json()["items"]
    by_id = {tx["id"]: tx for tx in items}
    assert by_id[uncategorized["id"]]["category_id"] == supermercado_id
    assert by_id[already_categorized["id"]]["category_id"] == ocio_id


def test_bulk_categorize_overwrites_and_ignores_foreign_ids(
    client: TestClient, auth_headers, make_account
) -> None:
    headers_a, user_a = auth_headers()
    headers_b, user_b = auth_headers()
    account_a = make_account(user_a)
    account_b = make_account(user_b)
    ocio_id = _find_category(client, headers_a, "expense", "Ocio", "Juegos/Aficiones")
    sin_clasificar_id = _find_category(
        client, headers_b, "expense", "Finanzas y Otros", "Sin Clasificar"
    )

    tx_a = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account_a.id,
            "amount": "-5.00",
            "direction": "expense",
            "posted_at": "2026-09-01",
        },
        headers=headers_a,
    ).json()
    tx_b = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account_b.id,
            "amount": "-5.00",
            "direction": "expense",
            "posted_at": "2026-09-01",
        },
        headers=headers_b,
    ).json()

    response = client.post(
        "/api/v1/transactions/bulk-categorize",
        json={"transaction_ids": [tx_a["id"], tx_b["id"]], "category_id": ocio_id},
        headers=headers_a,
    )
    assert response.json()["updated_count"] == 1

    items_b = client.get("/api/v1/transactions/", headers=headers_b).json()["items"]
    assert items_b[0]["id"] == tx_b["id"]
    assert items_b[0]["category_id"] == sin_clasificar_id
