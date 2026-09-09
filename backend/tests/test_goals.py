from datetime import date, timedelta

from fastapi.testclient import TestClient


def test_create_goal_and_list(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    created = client.post(
        "/api/v1/goals/",
        json={"name": "Fondo de emergencia", "target_amount": "3000.00"},
        headers=headers,
    )
    assert created.status_code == 201
    body = created.json()
    assert body["current_amount"] == "0"
    assert body["pct"] == 0.0
    assert body["status"] == "active"

    listed = client.get("/api/v1/goals/", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_negative_or_zero_target_amount_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.post(
        "/api/v1/goals/", json={"name": "Meta", "target_amount": "0"}, headers=headers
    )
    assert response.status_code == 422


def test_contribution_updates_current_amount_and_pct(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    goal = client.post(
        "/api/v1/goals/", json={"name": "Viaje", "target_amount": "1000.00"}, headers=headers
    ).json()

    contribution = client.post(
        f"/api/v1/goals/{goal['id']}/contributions",
        json={"amount": "250.00", "contributed_at": "2026-03-01"},
        headers=headers,
    )
    assert contribution.status_code == 201

    refreshed = client.get("/api/v1/goals/", headers=headers).json()[0]
    assert refreshed["current_amount"] == "250.00"
    assert refreshed["pct"] == 25.0
    assert refreshed["status"] == "active"


def test_goal_marked_completed_when_target_reached(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    goal = client.post(
        "/api/v1/goals/", json={"name": "Bici", "target_amount": "300.00"}, headers=headers
    ).json()

    client.post(
        f"/api/v1/goals/{goal['id']}/contributions",
        json={"amount": "300.00", "contributed_at": "2026-03-01"},
        headers=headers,
    )

    refreshed = client.get("/api/v1/goals/", headers=headers).json()[0]
    assert refreshed["status"] == "completed"
    assert refreshed["pct"] == 100.0


def test_negative_contribution_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    goal = client.post(
        "/api/v1/goals/", json={"name": "Meta", "target_amount": "100.00"}, headers=headers
    ).json()

    response = client.post(
        f"/api/v1/goals/{goal['id']}/contributions",
        json={"amount": "0", "contributed_at": "2026-03-01"},
        headers=headers,
    )
    assert response.status_code == 422


def test_list_and_delete_contribution(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    goal = client.post(
        "/api/v1/goals/", json={"name": "Meta", "target_amount": "1000.00"}, headers=headers
    ).json()
    contribution = client.post(
        f"/api/v1/goals/{goal['id']}/contributions",
        json={"amount": "100.00", "contributed_at": "2026-03-01"},
        headers=headers,
    ).json()

    listed = client.get(f"/api/v1/goals/{goal['id']}/contributions", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    deleted = client.delete(
        f"/api/v1/goals/{goal['id']}/contributions/{contribution['id']}", headers=headers
    )
    assert deleted.status_code == 204

    refreshed = client.get("/api/v1/goals/", headers=headers).json()[0]
    assert refreshed["current_amount"] == "0"


def test_linked_account_must_belong_to_user(client: TestClient, auth_headers, make_account) -> None:
    headers_a, user_a = auth_headers()
    _, user_b = auth_headers()
    account_b = make_account(user_b)

    response = client.post(
        "/api/v1/goals/",
        json={"name": "Meta", "target_amount": "100.00", "linked_account_id": account_b.id},
        headers=headers_a,
    )
    assert response.status_code == 404


def test_update_and_delete_goal(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    goal = client.post(
        "/api/v1/goals/", json={"name": "Meta", "target_amount": "500.00"}, headers=headers
    ).json()

    updated = client.patch(
        f"/api/v1/goals/{goal['id']}",
        json={"target_amount": "600.00", "status": "archived"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["target_amount"] == "600.00"
    assert updated.json()["status"] == "archived"

    deleted = client.delete(f"/api/v1/goals/{goal['id']}", headers=headers)
    assert deleted.status_code == 204
    assert client.get("/api/v1/goals/", headers=headers).json() == []


def test_projection_insufficient_data_for_new_goal(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    goal = client.post(
        "/api/v1/goals/", json={"name": "Meta nueva", "target_amount": "1000.00"}, headers=headers
    ).json()

    response = client.get(f"/api/v1/goals/{goal['id']}/projection", headers=headers)
    assert response.status_code == 200
    body = response.json()
    assert body["has_enough_data"] is False
    assert body["projected_date"] is None


def test_projection_already_completed_goal(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    goal = client.post(
        "/api/v1/goals/", json={"name": "Meta chica", "target_amount": "50.00"}, headers=headers
    ).json()
    client.post(
        f"/api/v1/goals/{goal['id']}/contributions",
        json={"amount": "50.00", "contributed_at": date.today().isoformat()},
        headers=headers,
    )

    response = client.get(f"/api/v1/goals/{goal['id']}/projection", headers=headers)
    body = response.json()
    assert body["has_enough_data"] is True
    assert body["months_remaining"] == 0
    assert body["projected_date"] == date.today().isoformat()


def test_projection_estimates_date_from_recent_pace(
    client: TestClient, auth_headers, db_session
) -> None:
    from app.models.savings_goal import SavingsGoal

    headers, user = auth_headers()
    goal = client.post(
        "/api/v1/goals/", json={"name": "Meta con historia", "target_amount": "900.00"}, headers=headers
    ).json()

    # forzar que la meta se haya creado hace >3 meses para que el proyector
    # tenga 3 meses calendario completos que mirar
    db_goal = db_session.query(SavingsGoal).filter(SavingsGoal.id == goal["id"]).one()
    db_goal.created_at = db_goal.created_at - timedelta(days=130)
    db_session.commit()

    today = date.today()
    # aportar 100 en cada uno de los 3 meses calendario completos anteriores
    for i in (1, 2, 3):
        month = today.month - i
        year = today.year
        while month <= 0:
            month += 12
            year -= 1
        contributed_at = date(year, month, 15)
        client.post(
            f"/api/v1/goals/{goal['id']}/contributions",
            json={"amount": "100.00", "contributed_at": contributed_at.isoformat()},
            headers=headers,
        )

    response = client.get(f"/api/v1/goals/{goal['id']}/projection", headers=headers)
    body = response.json()
    assert body["has_enough_data"] is True
    assert body["monthly_pace"] == "100.00"
    assert body["months_remaining"] == 6


def test_goals_isolated_between_users(client: TestClient, auth_headers) -> None:
    headers_a, _ = auth_headers()
    headers_b, _ = auth_headers()
    goal = client.post(
        "/api/v1/goals/", json={"name": "Meta A", "target_amount": "100.00"}, headers=headers_a
    ).json()

    forbidden = client.get(f"/api/v1/goals/{goal['id']}/projection", headers=headers_b)
    assert forbidden.status_code == 404

    listed_b = client.get("/api/v1/goals/", headers=headers_b).json()
    assert listed_b == []
