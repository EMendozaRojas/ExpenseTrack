from fastapi.testclient import TestClient

from app.models.category import Category


def test_monthly_summary_groups_by_category(
    client: TestClient, auth_headers, make_account, db_session
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    category = Category(name="Comida", owner_id=user.id)
    db_session.add(category)
    db_session.commit()
    db_session.refresh(category)

    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-12.50",
            "direction": "expense",
            "posted_at": "2026-09-04",
            "category_id": category.id,
        },
        headers=headers,
    )
    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-7.50",
            "direction": "expense",
            "posted_at": "2026-09-20",
            "category_id": category.id,
        },
        headers=headers,
    )
    # income and a different month should not count
    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "1000.00",
            "direction": "income",
            "posted_at": "2026-09-05",
        },
        headers=headers,
    )
    client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-5.00",
            "direction": "expense",
            "posted_at": "2026-10-01",
            "category_id": category.id,
        },
        headers=headers,
    )

    response = client.get(
        "/api/v1/expenses/summary", params={"year": 2026, "month": 9}, headers=headers
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == "20.00"
    assert body["by_category"] == [
        {"category_id": category.id, "category_name": "Comida", "total": "20.00"}
    ]


def test_monthly_summary_empty(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.get(
        "/api/v1/expenses/summary", params={"year": 2026, "month": 1}, headers=headers
    )
    assert response.status_code == 200
    assert response.json() == {"year": 2026, "month": 1, "total": "0", "by_category": []}
