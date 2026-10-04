from datetime import date

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
        "/api/v1/budgets/", json={"category_id": category_id, "amount": "100.00"}, headers=headers
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
        "/api/v1/budgets/", json={"category_id": category_id, "amount": "100.00"}, headers=headers
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
        "/api/v1/budgets/", json={"category_id": category_id, "amount": "100.00"}, headers=headers
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
        "/api/v1/budgets/", json={"category_id": category_id, "amount": "100.00"}, headers=headers_a
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
