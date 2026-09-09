from fastapi.testclient import TestClient


def _find_category(
    client: TestClient, headers: dict[str, str], kind: str, root_name: str, sub_name: str | None = None
) -> int:
    roots = client.get("/api/v1/categories/", params={"kind": kind}, headers=headers).json()
    root = next(r for r in roots if r["name"] == root_name)
    if sub_name is None:
        return root["id"]
    sub = next(c for c in root["children"] if c["name"] == sub_name)
    return sub["id"]


def _create_expense(
    client: TestClient, headers: dict[str, str], account_id: int, amount: str, posted_at: str, category_id: int
) -> None:
    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account_id,
            "amount": amount,
            "direction": "expense",
            "posted_at": posted_at,
            "category_id": category_id,
        },
        headers=headers,
    )
    assert response.status_code == 201


def test_create_budget_and_list_status_ok(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    created = client.post(
        "/api/v1/budgets/", json={"category_id": supermercado_id, "amount": "200.00"}, headers=headers
    )
    assert created.status_code == 201
    assert created.json()["category_name"] == "Supermercado"

    _create_expense(client, headers, account.id, "-50.00", "2026-03-05", supermercado_id)

    listed = client.get("/api/v1/budgets/", params={"year": 2026, "month": 3}, headers=headers)
    assert listed.status_code == 200
    body = listed.json()[0]
    assert body["spent"] == "50.00"
    assert body["pct"] == 25.0
    assert body["status"] == "ok"


def test_status_warning_and_exceeded_thresholds(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    client.post(
        "/api/v1/budgets/", json={"category_id": supermercado_id, "amount": "100.00"}, headers=headers
    )

    _create_expense(client, headers, account.id, "-85.00", "2026-03-05", supermercado_id)
    warning = client.get("/api/v1/budgets/", params={"year": 2026, "month": 3}, headers=headers).json()[0]
    assert warning["status"] == "warning"

    _create_expense(client, headers, account.id, "-20.00", "2026-03-06", supermercado_id)
    exceeded = client.get("/api/v1/budgets/", params={"year": 2026, "month": 3}, headers=headers).json()[0]
    assert exceeded["status"] == "exceeded"
    assert exceeded["spent"] == "105.00"


def test_root_budget_rolls_up_subcategory_spend(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    vivienda_root_id = _find_category(client, headers, "expense", "Vivienda")
    alquiler_id = _find_category(client, headers, "expense", "Vivienda", "Alquiler/Hipoteca")
    suministros_id = _find_category(client, headers, "expense", "Vivienda", "Suministros (Luz/Agua/Gas)")

    client.post(
        "/api/v1/budgets/", json={"category_id": vivienda_root_id, "amount": "1000.00"}, headers=headers
    )
    _create_expense(client, headers, account.id, "-700.00", "2026-03-01", alquiler_id)
    _create_expense(client, headers, account.id, "-90.00", "2026-03-02", suministros_id)

    body = client.get("/api/v1/budgets/", params={"year": 2026, "month": 3}, headers=headers).json()[0]
    assert body["spent"] == "790.00"


def test_root_and_subcategory_budgets_are_independent(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    vivienda_root_id = _find_category(client, headers, "expense", "Vivienda")
    alquiler_id = _find_category(client, headers, "expense", "Vivienda", "Alquiler/Hipoteca")

    client.post(
        "/api/v1/budgets/", json={"category_id": vivienda_root_id, "amount": "1000.00"}, headers=headers
    )
    sub_budget = client.post(
        "/api/v1/budgets/", json={"category_id": alquiler_id, "amount": "800.00"}, headers=headers
    )
    assert sub_budget.status_code == 201

    _create_expense(client, headers, account.id, "-700.00", "2026-03-01", alquiler_id)

    results = {
        b["category_id"]: b
        for b in client.get("/api/v1/budgets/", params={"year": 2026, "month": 3}, headers=headers).json()
    }
    assert results[vivienda_root_id]["spent"] == "700.00"
    assert results[alquiler_id]["spent"] == "700.00"


def test_duplicate_budget_for_same_category_rejected(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    first = client.post(
        "/api/v1/budgets/", json={"category_id": supermercado_id, "amount": "200.00"}, headers=headers
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/budgets/", json={"category_id": supermercado_id, "amount": "300.00"}, headers=headers
    )
    assert second.status_code == 409


def test_income_category_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    nomina_id = _find_category(client, headers, "income", "Nómina y salario", "Nómina")

    response = client.post(
        "/api/v1/budgets/", json={"category_id": nomina_id, "amount": "100.00"}, headers=headers
    )
    assert response.status_code == 404


def test_negative_or_zero_amount_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    response = client.post(
        "/api/v1/budgets/", json={"category_id": supermercado_id, "amount": "0"}, headers=headers
    )
    assert response.status_code == 422


def test_update_and_delete_budget(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    created = client.post(
        "/api/v1/budgets/", json={"category_id": supermercado_id, "amount": "200.00"}, headers=headers
    ).json()

    updated = client.patch(
        f"/api/v1/budgets/{created['id']}", json={"amount": "250.00"}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["amount"] == "250.00"

    deleted = client.delete(f"/api/v1/budgets/{created['id']}", headers=headers)
    assert deleted.status_code == 204

    listed = client.get("/api/v1/budgets/", params={"year": 2026, "month": 3}, headers=headers).json()
    assert listed == []


def test_budgets_isolated_between_users(client: TestClient, auth_headers) -> None:
    headers_a, _ = auth_headers()
    headers_b, _ = auth_headers()
    supermercado_id = _find_category(client, headers_a, "expense", "Alimentación", "Supermercado")

    created = client.post(
        "/api/v1/budgets/", json={"category_id": supermercado_id, "amount": "200.00"}, headers=headers_a
    ).json()

    forbidden_update = client.patch(
        f"/api/v1/budgets/{created['id']}", json={"amount": "1.00"}, headers=headers_b
    )
    assert forbidden_update.status_code == 404

    listed_b = client.get("/api/v1/budgets/", params={"year": 2026, "month": 3}, headers=headers_b).json()
    assert listed_b == []
