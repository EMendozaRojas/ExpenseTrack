from datetime import date, timedelta

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
    category_id: int,
    note: str | None = None,
) -> None:
    payload = {
        "account_id": account_id,
        "amount": amount,
        "direction": "expense",
        "posted_at": posted_at,
        "category_id": category_id,
    }
    if note:
        payload["note"] = note
    response = client.post("/api/v1/transactions/", json=payload, headers=headers)
    assert response.status_code == 201


def test_recurring_series_detected_with_monthly_cadence(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    streaming_id = _find_category(client, headers, "expense", "Suscripciones", "Streaming")

    today = date.today()
    for months_ago in (0, 1, 2, 3):
        posted = today.replace(day=1) - timedelta(days=30 * months_ago)
        _create_expense(
            client, headers, account.id, "-12.99", posted.isoformat(), streaming_id, note="NETFLIX"
        )

    response = client.get("/api/v1/insights/recurring", headers=headers)
    assert response.status_code == 200
    body = response.json()
    netflix = next(s for s in body if "NETFLIX" in s["label"])
    assert netflix["occurrences"] == 4
    assert netflix["direction"] == "expense"
    assert netflix["cadence_label"] == "mensual"
    assert netflix["dismissed"] is False


def test_recurring_series_with_only_two_occurrences_not_detected(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    streaming_id = _find_category(client, headers, "expense", "Suscripciones", "Streaming")

    today = date.today()
    for months_ago in (0, 1):
        posted = today.replace(day=1) - timedelta(days=30 * months_ago)
        _create_expense(
            client, headers, account.id, "-9.99", posted.isoformat(), streaming_id, note="SPOTIFY"
        )

    body = client.get("/api/v1/insights/recurring", headers=headers).json()
    assert all("SPOTIFY" not in s["label"] for s in body)


def test_recurring_series_with_irregular_amount_not_detected(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    today = date.today()
    amounts = ["-10.00", "-50.00", "-90.00"]
    for months_ago, amount in enumerate(amounts):
        posted = today.replace(day=1) - timedelta(days=30 * months_ago)
        _create_expense(
            client,
            headers,
            account.id,
            amount,
            posted.isoformat(),
            supermercado_id,
            note="MERCADONA VARIABLE",
        )

    body = client.get("/api/v1/insights/recurring", headers=headers).json()
    assert all("MERCADONA VARIABLE" not in s["label"] for s in body)


def test_dismiss_and_restore_recurring_series(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    streaming_id = _find_category(client, headers, "expense", "Suscripciones", "Streaming")

    today = date.today()
    for months_ago in (0, 1, 2):
        posted = today.replace(day=1) - timedelta(days=30 * months_ago)
        _create_expense(
            client, headers, account.id, "-12.99", posted.isoformat(), streaming_id, note="NETFLIX"
        )

    series = client.get("/api/v1/insights/recurring", headers=headers).json()
    key = next(s for s in series if "NETFLIX" in s["label"])["key"]

    dismiss = client.post(
        "/api/v1/insights/recurring/dismiss", json={"series_key": key}, headers=headers
    )
    assert dismiss.status_code == 204

    after_dismiss = client.get("/api/v1/insights/recurring", headers=headers).json()
    netflix = next(s for s in after_dismiss if s["key"] == key)
    assert netflix["dismissed"] is True

    restore = client.post(
        "/api/v1/insights/recurring/restore", json={"series_key": key}, headers=headers
    )
    assert restore.status_code == 204

    after_restore = client.get("/api/v1/insights/recurring", headers=headers).json()
    netflix2 = next(s for s in after_restore if s["key"] == key)
    assert netflix2["dismissed"] is False


def test_ant_spending_detects_frequent_small_expenses(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    cafeterias_id = _find_category(client, headers, "expense", "Restauración", "Cafeterías")

    for day in range(1, 10):
        _create_expense(client, headers, account.id, "-3.50", f"2026-03-{day:02d}", cafeterias_id)

    response = client.get(
        "/api/v1/insights/ant-spending", params={"year": 2026, "month": 3}, headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["occurrences"] == 9
    assert body[0]["aggregate"] == "31.50"


def test_ant_spending_ignores_groups_below_thresholds(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    cafeterias_id = _find_category(client, headers, "expense", "Restauración", "Cafeterías")

    # solo 2 movimientos: no llega al mínimo de ocurrencias (5)
    _create_expense(client, headers, account.id, "-3.50", "2026-03-01", cafeterias_id)
    _create_expense(client, headers, account.id, "-3.50", "2026-03-02", cafeterias_id)

    body = client.get(
        "/api/v1/insights/ant-spending", params={"year": 2026, "month": 3}, headers=headers
    ).json()
    assert body == []


def test_ant_spending_ignores_large_transactions(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    for day in range(1, 6):
        _create_expense(
            client, headers, account.id, "-50.00", f"2026-03-{day:02d}", supermercado_id
        )

    body = client.get(
        "/api/v1/insights/ant-spending", params={"year": 2026, "month": 3}, headers=headers
    ).json()
    assert body == []


def test_get_and_update_insight_settings(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    defaults = client.get("/api/v1/insights/settings", headers=headers)
    assert defaults.status_code == 200
    assert defaults.json() == {
        "ant_max_amount": "10.00",
        "ant_min_occurrences": 5,
        "ant_min_aggregate": "30.00",
    }

    updated = client.patch(
        "/api/v1/insights/settings",
        json={"ant_max_amount": "15.00", "ant_min_occurrences": 3},
        headers=headers,
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["ant_max_amount"] == "15.00"
    assert body["ant_min_occurrences"] == 3
    assert body["ant_min_aggregate"] == "30.00"


def test_ant_spending_respects_custom_settings(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    cafeterias_id = _find_category(client, headers, "expense", "Restauración", "Cafeterías")

    client.patch(
        "/api/v1/insights/settings",
        json={"ant_min_occurrences": 3, "ant_min_aggregate": "5.00"},
        headers=headers,
    )
    for day in range(1, 4):
        _create_expense(client, headers, account.id, "-2.00", f"2026-03-{day:02d}", cafeterias_id)

    body = client.get(
        "/api/v1/insights/ant-spending", params={"year": 2026, "month": 3}, headers=headers
    ).json()
    assert len(body) == 1
    assert body[0]["occurrences"] == 3
