from datetime import UTC, date

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


def _budget_payload(category_id: int, amount: str) -> dict:
    today = date.today()
    return {"category_id": category_id, "year": today.year, "month": today.month, "amount": amount}


def test_no_notifications_for_new_user(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.get("/api/v1/notifications/", headers=headers)
    assert response.status_code == 200
    assert response.json() == []

    count = client.get("/api/v1/notifications/unread-count", headers=headers)
    assert count.json() == {"count": 0}


def test_budget_warning_notification_created_when_crossing_80_pct(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    client.post(
        "/api/v1/budgets/", json=_budget_payload(category_id, "100.00"), headers=headers
    )

    today = date.today().isoformat()
    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-85.00",
            "direction": "expense",
            "posted_at": today,
            "category_id": category_id,
        },
        headers=headers,
    )
    assert response.status_code == 201

    notifications = client.get("/api/v1/notifications/", headers=headers).json()
    assert len(notifications) == 1
    assert notifications[0]["type"] == "budget_warning"
    assert notifications[0]["is_read"] is False

    count = client.get("/api/v1/notifications/unread-count", headers=headers).json()
    assert count["count"] == 1


def test_budget_exceeded_replaces_does_not_duplicate_warning(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    client.post(
        "/api/v1/budgets/", json=_budget_payload(category_id, "100.00"), headers=headers
    )

    today = date.today().isoformat()
    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-85.00",
            "direction": "expense",
            "posted_at": today,
            "category_id": category_id,
        },
        headers=headers,
    )
    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-30.00",
            "direction": "expense",
            "posted_at": today,
            "category_id": category_id,
        },
        headers=headers,
    )

    notifications = client.get("/api/v1/notifications/", headers=headers).json()
    types = {n["type"] for n in notifications}
    assert types == {"budget_warning", "budget_exceeded"}

    # una segunda transacción que lo mantiene por encima de 100% no duplica el aviso
    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-5.00",
            "direction": "expense",
            "posted_at": today,
            "category_id": category_id,
        },
        headers=headers,
    )
    notifications_after = client.get("/api/v1/notifications/", headers=headers).json()
    assert len(notifications_after) == 2


def test_goal_near_and_reached_notifications(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    goal = client.post(
        "/api/v1/goals/",
        json={"name": "Viaje", "target_amount": "100.00"},
        headers=headers,
    ).json()

    client.post(
        f"/api/v1/goals/{goal['id']}/contributions",
        json={"amount": "85.00", "contributed_at": date.today().isoformat()},
        headers=headers,
    )

    notifications = client.get("/api/v1/notifications/", headers=headers).json()
    assert [n["type"] for n in notifications] == ["goal_near"]

    client.post(
        f"/api/v1/goals/{goal['id']}/contributions",
        json={"amount": "20.00", "contributed_at": date.today().isoformat()},
        headers=headers,
    )

    notifications_after = client.get("/api/v1/notifications/", headers=headers).json()
    types = {n["type"] for n in notifications_after}
    assert types == {"goal_near", "goal_reached"}


def test_mark_notification_read_and_read_all(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    client.post(
        "/api/v1/budgets/", json=_budget_payload(category_id, "100.00"), headers=headers
    )
    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-85.00",
            "direction": "expense",
            "posted_at": date.today().isoformat(),
            "category_id": category_id,
        },
        headers=headers,
    )

    notification_id = client.get("/api/v1/notifications/", headers=headers).json()[0]["id"]

    read = client.post(f"/api/v1/notifications/{notification_id}/read", headers=headers)
    assert read.status_code == 200
    assert read.json()["is_read"] is True

    count = client.get("/api/v1/notifications/unread-count", headers=headers).json()
    assert count["count"] == 0

    mark_all = client.post("/api/v1/notifications/read-all", headers=headers)
    assert mark_all.status_code == 204


def test_notifications_isolated_between_users(client: TestClient, auth_headers, make_account) -> None:
    headers_a, user_a = auth_headers()
    headers_b, _ = auth_headers()
    account = make_account(user_a)
    category_id = _find_category(client, headers_a, "expense", "Alimentación", "Supermercado")
    client.post(
        "/api/v1/budgets/", json=_budget_payload(category_id, "100.00"), headers=headers_a
    )
    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-85.00",
            "direction": "expense",
            "posted_at": date.today().isoformat(),
            "category_id": category_id,
        },
        headers=headers_a,
    )

    notifications_b = client.get("/api/v1/notifications/", headers=headers_b).json()
    assert notifications_b == []


# --- Presupuestos mensuales: disparadores, revisión al entrar y resumen ------

OCTOBER_15 = date(2026, 10, 15)


def _monthly_budget(
    client: TestClient, headers, category_id: int, amount: str, year=2026, month=10
):
    response = client.post(
        "/api/v1/budgets/",
        json={"category_id": category_id, "year": year, "month": month, "amount": amount},
        headers=headers,
    )
    assert response.status_code == 201


def _expense(
    client: TestClient, headers, account_id: int, amount: str, posted_at: str, category_id: int
) -> int:
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
    return response.json()["id"]


def _types(client: TestClient, headers) -> list[str]:
    return sorted(n["type"] for n in client.get("/api/v1/notifications/", headers=headers).json())


def test_check_creates_missing_notification_without_duplicating(
    client: TestClient, auth_headers, make_account, set_today, db_session
) -> None:
    from decimal import Decimal

    from app.models.transaction import Transaction

    set_today(OCTOBER_15)
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    _monthly_budget(client, headers, category_id, "100.00")

    # Movimiento creado sin pasar por los disparadores de la API.
    db_session.add(
        Transaction(
            account_id=account.id,
            owner_id=user.id,
            amount=Decimal("-90.00"),
            direction="expense",
            posted_at=date(2026, 10, 3),
            category_id=category_id,
            source="manual",
        )
    )
    db_session.commit()
    assert _types(client, headers) == []

    assert client.post("/api/v1/notifications/check", headers=headers).status_code == 204
    assert _types(client, headers) == ["budget_warning"]

    client.post("/api/v1/notifications/check", headers=headers)
    assert _types(client, headers) == ["budget_warning"]


def test_one_notification_per_category_and_month_even_if_amount_changes(
    client: TestClient, auth_headers, make_account, set_today
) -> None:
    set_today(OCTOBER_15)
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    _monthly_budget(client, headers, category_id, "100.00")
    _expense(client, headers, account.id, "-85.00", "2026-10-02", category_id)

    client.put(f"/api/v1/budgets/{category_id}/2026-10", json={"amount": "500.00"}, headers=headers)
    client.put(f"/api/v1/budgets/{category_id}/2026-10", json={"amount": "100.00"}, headers=headers)
    assert _types(client, headers) == ["budget_warning"]


def test_lowering_amount_triggers_notification(
    client: TestClient, auth_headers, make_account, set_today
) -> None:
    set_today(OCTOBER_15)
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    _monthly_budget(client, headers, category_id, "500.00")
    _expense(client, headers, account.id, "-90.00", "2026-10-02", category_id)
    assert _types(client, headers) == []

    client.put(f"/api/v1/budgets/{category_id}/2026-10", json={"amount": "90.00"}, headers=headers)
    assert _types(client, headers) == ["budget_exceeded"]


def test_restoring_a_transaction_triggers_notification(
    client: TestClient, auth_headers, make_account, set_today, db_session
) -> None:
    from datetime import datetime
    from decimal import Decimal

    from app.models.transaction import Transaction

    set_today(OCTOBER_15)
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    _monthly_budget(client, headers, category_id, "100.00")
    trashed = Transaction(
        account_id=account.id,
        owner_id=user.id,
        amount=Decimal("-100.00"),
        direction="expense",
        posted_at=date(2026, 10, 2),
        category_id=category_id,
        source="manual",
        deleted_at=datetime.now(UTC),
    )
    db_session.add(trashed)
    db_session.commit()
    assert _types(client, headers) == []

    response = client.post(f"/api/v1/transactions/{trashed.id}/restore", headers=headers)
    assert response.status_code == 200
    assert _types(client, headers) == ["budget_exceeded"]


def test_bulk_categorize_triggers_notification(
    client: TestClient, auth_headers, make_account, set_today
) -> None:
    set_today(OCTOBER_15)
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    farmacia_id = _find_category(client, headers, "expense", "Salud", "Farmacia")
    _monthly_budget(client, headers, farmacia_id, "100.00")
    transaction_id = _expense(client, headers, account.id, "-85.00", "2026-10-03", supermercado_id)
    assert _types(client, headers) == []

    client.post(
        "/api/v1/transactions/bulk-categorize",
        json={"transaction_ids": [transaction_id], "category_id": farmacia_id},
        headers=headers,
    )
    assert _types(client, headers) == ["budget_warning"]


def test_import_commit_triggers_notification(
    client: TestClient, auth_headers, make_account, set_today
) -> None:
    set_today(OCTOBER_15)
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    _monthly_budget(client, headers, supermercado_id, "100.00")

    preview = client.post(
        "/api/v1/imports/",
        headers=headers,
        data={"account_id": str(account.id)},
        files={
            "file": (
                "extracto.csv",
                b"Fecha;Concepto;Importe\n2026-10-05;COMPRA EN MERCADONA 1;-85,00\n",
                "text/csv",
            )
        },
    ).json()
    assert _types(client, headers) == []

    committed = client.post(
        f"/api/v1/imports/{preview['id']}/commit", json={"strategy": "append_new"}, headers=headers
    )
    assert committed.status_code == 200
    assert _types(client, headers) == ["budget_warning"]


def test_past_months_never_notify(
    client: TestClient, auth_headers, make_account, set_today
) -> None:
    set_today(date(2026, 9, 1))
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    _monthly_budget(client, headers, category_id, "100.00", month=9)
    set_today(OCTOBER_15)
    # Septiembre se repite en octubre: lo quitamos para que solo cuente septiembre.
    client.delete(
        f"/api/v1/budgets/{category_id}/2026-10", params={"scope": "following"}, headers=headers
    )

    _expense(client, headers, account.id, "-150.00", "2026-09-20", category_id)
    client.post("/api/v1/notifications/check", headers=headers)

    assert "budget_exceeded" not in _types(client, headers)
    september = client.get(
        "/api/v1/budgets/", params={"year": 2026, "month": 9}, headers=headers
    ).json()[0]
    assert september["status"] == "exceeded"


def test_month_summary_created_once(
    client: TestClient, auth_headers, make_account, set_today
) -> None:
    set_today(date(2026, 9, 1))
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    farmacia_id = _find_category(client, headers, "expense", "Salud", "Farmacia")
    _monthly_budget(client, headers, supermercado_id, "100.00", month=9)
    _monthly_budget(client, headers, farmacia_id, "50.00", month=9)
    _expense(client, headers, account.id, "-120.00", "2026-09-10", supermercado_id)
    set_today(date(2026, 10, 2))

    client.post("/api/v1/notifications/check", headers=headers)
    client.post("/api/v1/notifications/check", headers=headers)

    summaries = [
        n for n in client.get("/api/v1/notifications/", headers=headers).json()
        if n["type"] == "budget_month_summary"
    ]
    assert len(summaries) == 1
    assert summaries[0]["title"] == "Resumen de septiembre: 1 de 2 presupuestos cumplidos"
    assert "Supermercado (120%)" in summaries[0]["body"]


def test_no_month_summary_without_budgets(client: TestClient, auth_headers, set_today) -> None:
    set_today(OCTOBER_15)
    headers, _ = auth_headers()

    client.post("/api/v1/notifications/check", headers=headers)
    assert _types(client, headers) == []
