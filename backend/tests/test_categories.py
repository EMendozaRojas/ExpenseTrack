from fastapi.testclient import TestClient


def test_list_includes_system_categories(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.get("/api/v1/categories/", params={"kind": "expense"}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    names = {root["name"] for root in body}
    assert "Alimentación" in names
    alimentacion = next(root for root in body if root["name"] == "Alimentación")
    assert any(child["name"] == "Supermercado" for child in alimentacion["children"])


def test_create_subcategory(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    roots = client.get("/api/v1/categories/", params={"kind": "expense"}, headers=headers).json()
    ocio = next(root for root in roots if root["name"] == "Ocio")

    response = client.post(
        "/api/v1/categories/",
        json={"name": "Videojuegos", "kind": "expense", "parent_id": ocio["id"]},
        headers=headers,
    )
    assert response.status_code == 201
    body = response.json()
    assert body["parent_id"] == ocio["id"]
    assert body["kind"] == "expense"


def test_reject_second_level_subcategory(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    roots = client.get("/api/v1/categories/", params={"kind": "expense"}, headers=headers).json()
    suscripciones = next(root for root in roots if root["name"] == "Suscripciones")
    streaming = next(child for child in suscripciones["children"] if child["name"] == "Streaming")

    response = client.post(
        "/api/v1/categories/",
        json={"name": "Netflix", "kind": "expense", "parent_id": streaming["id"]},
        headers=headers,
    )
    assert response.status_code == 422


def test_duplicate_name_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    first = client.post(
        "/api/v1/categories/", json={"name": "Cripto", "kind": "expense"}, headers=headers
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/categories/", json={"name": "Cripto", "kind": "expense"}, headers=headers
    )
    assert second.status_code == 409


def test_cannot_delete_system_category(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    roots = client.get("/api/v1/categories/", params={"kind": "expense"}, headers=headers).json()
    ocio = next(root for root in roots if root["name"] == "Ocio")

    response = client.delete(f"/api/v1/categories/{ocio['id']}", headers=headers)
    assert response.status_code == 404


def test_delete_reassigns_transactions_and_subcategories(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    root = client.post(
        "/api/v1/categories/", json={"name": "Personalizada", "kind": "expense"}, headers=headers
    ).json()
    sub = client.post(
        "/api/v1/categories/",
        json={"name": "Sub", "kind": "expense", "parent_id": root["id"]},
        headers=headers,
    ).json()
    tx = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-5.00",
            "direction": "expense",
            "posted_at": "2026-09-01",
            "category_id": sub["id"],
        },
        headers=headers,
    ).json()

    delete = client.delete(f"/api/v1/categories/{sub['id']}", headers=headers)
    assert delete.status_code == 200
    assert delete.json() == {"reassigned_transactions": 1, "reassigned_subcategories": 0}

    roots = client.get("/api/v1/categories/", params={"kind": "expense"}, headers=headers).json()
    finanzas = next(r for r in roots if r["name"] == "Finanzas y Otros")
    sin_clasificar = next(c for c in finanzas["children"] if c["name"] == "Sin Clasificar")

    updated_tx = client.get("/api/v1/transactions/", headers=headers).json()["items"]
    assert updated_tx[0]["id"] == tx["id"]
    assert updated_tx[0]["category_id"] == sin_clasificar["id"]
