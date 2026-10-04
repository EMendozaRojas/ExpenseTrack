from datetime import date

from fastapi.testclient import TestClient


def _find_category(
    client: TestClient, headers: dict[str, str], kind: str, root_name: str, sub_name: str
) -> int:
    roots = client.get("/api/v1/categories/", params={"kind": kind}, headers=headers).json()
    root = next(r for r in roots if r["name"] == root_name)
    sub = next(c for c in root["children"] if c["name"] == sub_name)
    return sub["id"]


def _create_expense(
    client: TestClient,
    headers: dict[str, str],
    account_id: int,
    amount: str,
    posted_at: str,
    category_id: int | None = None,
) -> None:
    payload = {
        "account_id": account_id,
        "amount": amount,
        "direction": "expense",
        "posted_at": posted_at,
    }
    if category_id is not None:
        payload["category_id"] = category_id
    response = client.post("/api/v1/transactions/", json=payload, headers=headers)
    assert response.status_code == 201


def test_income_expense_net_and_status(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "1000.00",
            "direction": "income",
            "posted_at": "2026-03-05",
        },
        headers=headers,
    )
    _create_expense(client, headers, account.id, "-400.00", "2026-03-10", supermercado_id)

    response = client.get("/api/v1/dashboard/summary", params={"year": 2026, "month": 3}, headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["income_total"] == "1000.00"
    assert body["expense_total"] == "400.00"
    assert body["net_total"] == "600.00"
    assert body["net_status"] == "a_favor"


def test_net_status_en_contra_when_negative(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "100.00",
            "direction": "income",
            "posted_at": "2026-03-05",
        },
        headers=headers,
    )
    _create_expense(client, headers, account.id, "-500.00", "2026-03-10", supermercado_id)

    response = client.get("/api/v1/dashboard/summary", params={"year": 2026, "month": 3}, headers=headers)
    body = response.json()
    assert body["net_total"] == "-400.00"
    assert body["net_status"] == "en_contra"


def test_by_category_rolls_up_to_root_and_includes_uncategorized(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    restaurantes_id = _find_category(client, headers, "expense", "Restauración", "Restaurantes")

    _create_expense(client, headers, account.id, "-30.00", "2026-03-01", supermercado_id)
    _create_expense(client, headers, account.id, "-20.00", "2026-03-02", supermercado_id)
    _create_expense(client, headers, account.id, "-10.00", "2026-03-03", restaurantes_id)
    # sin categoría explícita y sin regla que aplique -> Finanzas y Otros / Sin Clasificar
    _create_expense(client, headers, account.id, "-5.00", "2026-03-04", None)

    response = client.get("/api/v1/dashboard/summary", params={"year": 2026, "month": 3}, headers=headers)
    body = response.json()
    by_category = {node["category_name"]: node for node in body["by_category"]}

    assert by_category["Alimentación"]["total"] == "50.00"
    assert {s["category_name"] for s in by_category["Alimentación"]["subcategories"]} == {
        "Supermercado"
    }
    assert by_category["Restauración"]["total"] == "10.00"
    finanzas = by_category["Finanzas y Otros"]
    assert finanzas["total"] == "5.00"
    assert any(s["category_name"] == "Sin Clasificar" and s["total"] == "5.00" for s in finanzas["subcategories"])
    assert body["expense_total"] == "65.00"


def test_fixed_vs_variable_split(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    alquiler_id = _find_category(client, headers, "expense", "Vivienda", "Alquiler/Hipoteca")
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    _create_expense(client, headers, account.id, "-800.00", "2026-03-01", alquiler_id)
    _create_expense(client, headers, account.id, "-100.00", "2026-03-02", supermercado_id)

    response = client.get("/api/v1/dashboard/summary", params={"year": 2026, "month": 3}, headers=headers)
    body = response.json()
    assert body["fixed_total"] == "800.00"
    assert body["variable_total"] == "100.00"


def test_incomplete_data_false_for_closed_past_month(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    _create_expense(client, headers, account.id, "-10.00", "2020-01-01", supermercado_id)

    response = client.get("/api/v1/dashboard/summary", params={"year": 2020, "month": 1}, headers=headers)
    assert response.json()["incomplete_data"] is False


def test_incomplete_data_false_when_recent_movement_exists(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    today = date.today()
    _create_expense(client, headers, account.id, "-10.00", today.isoformat(), supermercado_id)

    response = client.get(
        "/api/v1/dashboard/summary",
        params={"year": today.year, "month": today.month},
        headers=headers,
    )
    body = response.json()
    assert body["incomplete_data"] is False
    assert body["last_transaction_date"] == today.isoformat()


def test_no_transactions_this_month_is_incomplete(
    client: TestClient, auth_headers
) -> None:
    headers, _ = auth_headers()
    today = date.today()

    response = client.get(
        "/api/v1/dashboard/summary",
        params={"year": today.year, "month": today.month},
        headers=headers,
    )
    body = response.json()
    assert body["incomplete_data"] is True
    assert body["last_transaction_date"] is None


def test_dashboard_filters_by_account(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account_a = make_account(user, name="Efectivo", type="cash")
    account_b = make_account(user, name="Banco", type="checking")

    _create_expense(client, headers, account_a.id, "-10.00", "2026-09-05")
    _create_expense(client, headers, account_b.id, "-25.00", "2026-09-05")

    combined = client.get(
        "/api/v1/dashboard/summary", params={"year": 2026, "month": 9}, headers=headers
    ).json()
    assert combined["expense_total"] == "35.00"

    only_a = client.get(
        "/api/v1/dashboard/summary",
        params={"year": 2026, "month": 9, "account_id": account_a.id},
        headers=headers,
    ).json()
    assert only_a["expense_total"] == "10.00"


def test_dashboard_rejects_account_from_another_user(
    client: TestClient, auth_headers, make_account
) -> None:
    headers_a, user_a = auth_headers()
    headers_b, _ = auth_headers()
    account_a = make_account(user_a)

    response = client.get(
        "/api/v1/dashboard/summary",
        params={"year": 2026, "month": 9, "account_id": account_a.id},
        headers=headers_b,
    )
    assert response.status_code == 404
