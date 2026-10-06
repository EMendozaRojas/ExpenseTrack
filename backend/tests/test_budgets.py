from datetime import date

import pytest
from fastapi.testclient import TestClient

TODAY = date(2026, 10, 15)


@pytest.fixture(autouse=True)
def _october(set_today) -> None:
    set_today(TODAY)


def _find_category(
    client: TestClient,
    headers: dict[str, str],
    kind: str,
    root_name: str,
    sub_name: str | None = None,
) -> int:
    roots = client.get("/api/v1/categories/", params={"kind": kind}, headers=headers).json()
    root = next(r for r in roots if r["name"] == root_name)
    if sub_name is None:
        return root["id"]
    sub = next(c for c in root["children"] if c["name"] == sub_name)
    return sub["id"]


def _create_expense(
    client: TestClient,
    headers: dict[str, str],
    account_id: int,
    amount: str,
    posted_at: str,
    category_id: int,
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


def _create_budget(
    client: TestClient,
    headers: dict[str, str],
    category_id: int,
    amount: str,
    year: int = 2026,
    month: int = 10,
    repeat: bool = True,
):
    return client.post(
        "/api/v1/budgets/",
        json={
            "category_id": category_id,
            "year": year,
            "month": month,
            "amount": amount,
            "repeat": repeat,
        },
        headers=headers,
    )


def _list(client: TestClient, headers: dict[str, str], year: int, month: int) -> dict[int, dict]:
    response = client.get(
        "/api/v1/budgets/", params={"year": year, "month": month}, headers=headers
    )
    assert response.status_code == 200
    return {b["category_id"]: b for b in response.json()}


def _amounts(
    client: TestClient, headers: dict[str, str], category_id: int, months: list[tuple[int, int]]
):
    result = []
    for year, month in months:
        budget = _list(client, headers, year, month).get(category_id)
        result.append(budget["amount"] if budget else None)
    return result


OCT_TO_JAN = [(2026, 10), (2026, 11), (2026, 12), (2027, 1)]


# --- Crear ---------------------------------------------------------------


def test_create_repeating_budget_on_root_category(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    alimentacion_id = _find_category(client, headers, "expense", "Alimentación")

    created = _create_budget(client, headers, alimentacion_id, "300.00")
    assert created.status_code == 201
    body = created.json()
    assert body["category_name"] == "Alimentación"
    assert body["month"] == "2026-10"
    assert body["repeats"] is True
    assert body["source"] == "series"
    assert body["editable"] is True

    assert _amounts(client, headers, alimentacion_id, OCT_TO_JAN) == ["300.00"] * 4
    assert alimentacion_id not in _list(client, headers, 2026, 9)


def test_create_one_month_budget(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    ocio_id = _find_category(client, headers, "expense", "Ocio")

    created = _create_budget(client, headers, ocio_id, "150.00", repeat=False)
    assert created.status_code == 201
    assert created.json()["repeats"] is False
    assert created.json()["source"] == "single"
    assert _amounts(client, headers, ocio_id, OCT_TO_JAN) == ["150.00", None, None, None]


def test_plan_a_future_month(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    ocio_id = _find_category(client, headers, "expense", "Ocio")

    assert (
        _create_budget(client, headers, ocio_id, "600.00", month=12, repeat=False).status_code
        == 201
    )
    assert _amounts(client, headers, ocio_id, OCT_TO_JAN) == [None, None, "600.00", None]


def test_create_budget_on_subcategory(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    streaming_id = _find_category(client, headers, "expense", "Suscripciones", "Streaming")

    created = _create_budget(client, headers, streaming_id, "30.00")
    assert created.status_code == 201
    assert created.json()["category_name"] == "Streaming"


def test_duplicate_budget_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    _create_budget(client, headers, category_id, "100.00")

    assert _create_budget(client, headers, category_id, "50.00", repeat=False).status_code == 409
    assert _create_budget(client, headers, category_id, "50.00", month=12).status_code == 409


def test_income_or_foreign_category_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    other_headers, _ = auth_headers()
    nomina_id = _find_category(client, headers, "income", "Nómina y salario", "Nómina")
    ocio_id = _find_category(client, headers, "expense", "Ocio")
    own_category = client.post(
        "/api/v1/categories/",
        json={"name": "Mi afición", "parent_id": ocio_id},
        headers=other_headers,
    ).json()

    assert _create_budget(client, headers, nomina_id, "100.00").status_code == 404
    assert _create_budget(client, headers, own_category["id"], "100.00").status_code == 404


def test_non_positive_amount_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    assert _create_budget(client, headers, category_id, "0").status_code == 422
    assert _create_budget(client, headers, category_id, "-10.00").status_code == 422


def test_cannot_create_in_past_month(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    assert _create_budget(client, headers, category_id, "100.00", month=9).status_code == 409


# --- Estado y gasto -------------------------------------------------------


def test_status_thresholds_and_subtree_roll_up(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    vivienda_id = _find_category(client, headers, "expense", "Vivienda")
    alquiler_id = _find_category(client, headers, "expense", "Vivienda", "Alquiler/Hipoteca")
    suministros_id = _find_category(
        client, headers, "expense", "Vivienda", "Suministros (Luz/Agua/Gas)"
    )
    _create_budget(client, headers, vivienda_id, "1000.00")
    _create_budget(client, headers, alquiler_id, "800.00")

    _create_expense(client, headers, account.id, "-700.00", "2026-10-01", alquiler_id)
    _create_expense(client, headers, account.id, "-100.00", "2026-10-02", suministros_id)

    budgets = _list(client, headers, 2026, 10)
    assert budgets[vivienda_id]["spent"] == "800.00"
    assert budgets[vivienda_id]["status"] == "warning"
    assert budgets[alquiler_id]["spent"] == "700.00"
    assert budgets[alquiler_id]["pct"] == 87.5

    _create_expense(client, headers, account.id, "-250.00", "2026-10-03", alquiler_id)
    assert _list(client, headers, 2026, 10)[vivienda_id]["status"] == "exceeded"


def test_each_month_starts_at_zero(
    client: TestClient, auth_headers, make_account, set_today
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    set_today(date(2026, 9, 10))
    _create_budget(client, headers, category_id, "300.00", month=9)
    _create_expense(client, headers, account.id, "-250.00", "2026-09-05", category_id)
    set_today(TODAY)

    october = _list(client, headers, 2026, 10)[category_id]
    assert october["spent"] == "0.00"
    assert october["amount"] == "300.00"


def test_late_correction_updates_past_month(
    client: TestClient, auth_headers, make_account, set_today
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    set_today(date(2026, 9, 10))
    _create_budget(client, headers, category_id, "100.00", month=9)
    set_today(TODAY)

    _create_expense(client, headers, account.id, "-120.00", "2026-09-20", category_id)

    september = _list(client, headers, 2026, 9)[category_id]
    assert september["spent"] == "120.00"
    assert september["amount"] == "100.00"
    assert september["status"] == "exceeded"
    assert september["editable"] is False


# --- Editar y borrar con alcance -------------------------------------------


def _put(client, headers, category_id, period, amount, scope="this", repeat=None):
    body = {"amount": amount, "scope": scope}
    if repeat is not None:
        body["repeat"] = repeat
    return client.put(f"/api/v1/budgets/{category_id}/{period}", json=body, headers=headers)


def test_change_only_this_month(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación")
    _create_budget(client, headers, category_id, "200.00")

    response = _put(client, headers, category_id, "2026-12", "400.00", scope="this")
    assert response.status_code == 200
    assert response.json()["source"] == "override"
    assert response.json()["repeats"] is True
    assert _amounts(client, headers, category_id, OCT_TO_JAN) == [
        "200.00",
        "200.00",
        "400.00",
        "200.00",
    ]


def test_change_this_month_and_following(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación")
    _create_budget(client, headers, category_id, "200.00")

    assert (
        _put(client, headers, category_id, "2026-11", "300.00", scope="following").status_code
        == 200
    )
    assert _amounts(client, headers, category_id, OCT_TO_JAN) == [
        "200.00",
        "300.00",
        "300.00",
        "300.00",
    ]


def test_planned_months_kept_when_editing_following(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación")
    _create_budget(client, headers, category_id, "200.00")
    _put(client, headers, category_id, "2026-12", "600.00", scope="this")

    planned = client.get(
        f"/api/v1/budgets/{category_id}/planned", params={"from": "2026-11"}, headers=headers
    ).json()
    assert planned == [{"month": "2026-12", "amount": "600.00", "kind": "override"}]

    _put(client, headers, category_id, "2026-11", "300.00", scope="following")
    assert _amounts(client, headers, category_id, OCT_TO_JAN) == [
        "200.00",
        "300.00",
        "600.00",
        "300.00",
    ]


def test_delete_only_this_month(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación")
    _create_budget(client, headers, category_id, "200.00")

    response = client.delete(
        f"/api/v1/budgets/{category_id}/2026-11", params={"scope": "this"}, headers=headers
    )
    assert response.status_code == 204
    assert _amounts(client, headers, category_id, OCT_TO_JAN) == [
        "200.00",
        None,
        "200.00",
        "200.00",
    ]

    # Se puede volver a crear un presupuesto de un solo mes en el mes saltado.
    assert (
        _create_budget(client, headers, category_id, "50.00", month=11, repeat=False).status_code
        == 201
    )
    assert _amounts(client, headers, category_id, OCT_TO_JAN) == [
        "200.00",
        "50.00",
        "200.00",
        "200.00",
    ]


def test_delete_this_month_and_following(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación")
    _create_budget(client, headers, category_id, "200.00")
    _put(client, headers, category_id, "2027-01", "600.00", scope="this")
    _put(client, headers, category_id, "2026-12", "250.00", scope="following")

    response = client.delete(
        f"/api/v1/budgets/{category_id}/2026-11", params={"scope": "following"}, headers=headers
    )
    assert response.status_code == 204
    assert _amounts(client, headers, category_id, OCT_TO_JAN) == ["200.00", None, None, None]

    # Ya no hay presupuesto en noviembre: se puede crear uno nuevo.
    assert _create_budget(client, headers, category_id, "90.00", month=11).status_code == 201


def test_delete_one_month_budget(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Ocio")
    _create_budget(client, headers, category_id, "150.00", repeat=False)

    assert (
        client.delete(f"/api/v1/budgets/{category_id}/2026-10", headers=headers).status_code == 204
    )
    assert (
        client.delete(f"/api/v1/budgets/{category_id}/2026-10", headers=headers).status_code == 404
    )


def test_stop_and_start_repeating(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación")
    _create_budget(client, headers, category_id, "200.00")

    assert _put(client, headers, category_id, "2026-11", "200.00", repeat=False).status_code == 200
    assert _amounts(client, headers, category_id, OCT_TO_JAN) == ["200.00", "200.00", None, None]

    restarted = _put(client, headers, category_id, "2026-11", "250.00", repeat=True)
    assert restarted.status_code == 200
    assert _amounts(client, headers, category_id, OCT_TO_JAN) == [
        "200.00",
        "250.00",
        "250.00",
        "250.00",
    ]


def test_one_month_budget_can_start_repeating(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Ocio")
    _create_budget(client, headers, category_id, "150.00", repeat=False)

    assert _put(client, headers, category_id, "2026-10", "150.00", repeat=True).status_code == 200
    assert _amounts(client, headers, category_id, OCT_TO_JAN) == ["150.00"] * 4


def test_past_months_are_read_only(client: TestClient, auth_headers, set_today) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación")
    set_today(date(2026, 9, 1))
    _create_budget(client, headers, category_id, "200.00", month=9)
    set_today(TODAY)

    assert _put(client, headers, category_id, "2026-09", "300.00").status_code == 409
    assert (
        client.delete(f"/api/v1/budgets/{category_id}/2026-09", headers=headers).status_code == 409
    )


def test_later_changes_do_not_rewrite_history(client: TestClient, auth_headers, set_today) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación")
    _create_budget(client, headers, category_id, "200.00")
    set_today(date(2026, 12, 3))

    _put(client, headers, category_id, "2026-12", "400.00", scope="following")
    assert _amounts(client, headers, category_id, OCT_TO_JAN) == [
        "200.00",
        "200.00",
        "400.00",
        "400.00",
    ]
    assert _list(client, headers, 2026, 10)[category_id]["editable"] is False


def test_update_missing_budget_returns_404(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    category_id = _find_category(client, headers, "expense", "Alimentación")

    assert _put(client, headers, category_id, "2026-10", "100.00").status_code == 404


# --- Ritmo -----------------------------------------------------------------


def test_pace_projects_end_of_month(
    client: TestClient, auth_headers, make_account, set_today
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    set_today(date(2026, 11, 10))
    _create_budget(client, headers, category_id, "300.00", month=11)
    _create_expense(client, headers, account.id, "-150.00", "2026-11-04", category_id)

    november = _list(client, headers, 2026, 11)[category_id]
    assert november["pace"] == {"projected": "450.00", "will_exceed": True}
    assert _list(client, headers, 2026, 12)[category_id]["pace"] is None

    set_today(date(2026, 11, 3))
    assert _list(client, headers, 2026, 11)[category_id]["pace"] is None


# --- Copiar del mes anterior ---------------------------------------------


def test_copy_from_previous_month(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    ocio_id = _find_category(client, headers, "expense", "Ocio")
    ropa_id = _find_category(client, headers, "expense", "Compras y Personal", "Ropa y Calzado")
    alimentacion_id = _find_category(client, headers, "expense", "Alimentación")
    _create_budget(client, headers, ocio_id, "150.00", repeat=False)
    _create_budget(client, headers, ropa_id, "100.00", repeat=False)
    _create_budget(client, headers, alimentacion_id, "300.00")

    preview = client.get(
        "/api/v1/budgets/copy-preview", params={"year": 2026, "month": 11}, headers=headers
    ).json()
    assert {item["category_id"]: item["amount"] for item in preview} == {
        ocio_id: "150.00",
        ropa_id: "100.00",
    }

    result = client.post(
        "/api/v1/budgets/copy",
        json={
            "year": 2026,
            "month": 11,
            "items": [
                {"category_id": ocio_id, "amount": "150.00"},
                {"category_id": ropa_id, "amount": "200.00"},
                {"category_id": alimentacion_id, "amount": "999.00"},
            ],
        },
        headers=headers,
    )
    assert result.status_code == 200
    assert sorted(result.json()["created"]) == sorted([ocio_id, ropa_id])
    assert result.json()["skipped"] == [alimentacion_id]

    november = _list(client, headers, 2026, 11)
    assert november[ropa_id]["amount"] == "200.00"
    assert november[ropa_id]["repeats"] is False
    assert november[alimentacion_id]["amount"] == "300.00"
    assert (
        client.get(
            "/api/v1/budgets/copy-preview", params={"year": 2026, "month": 11}, headers=headers
        ).json()
        == []
    )


def test_copy_into_past_month_rejected(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()
    ocio_id = _find_category(client, headers, "expense", "Ocio")

    response = client.post(
        "/api/v1/budgets/copy",
        json={"year": 2026, "month": 9, "items": [{"category_id": ocio_id, "amount": "10.00"}]},
        headers=headers,
    )
    assert response.status_code == 409


# --- Borrar una categoría conserva el historial ----------------------------


def test_deleting_category_keeps_budget_history(
    client: TestClient, auth_headers, make_account, set_today
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    ocio_id = _find_category(client, headers, "expense", "Ocio")
    gimnasio = client.post(
        "/api/v1/categories/",
        json={"name": "Gimnasio Barrio", "parent_id": ocio_id},
        headers=headers,
    ).json()
    set_today(date(2026, 9, 1))
    _create_budget(client, headers, gimnasio["id"], "40.00", month=9)
    _create_expense(client, headers, account.id, "-35.00", "2026-09-10", gimnasio["id"])
    set_today(TODAY)

    assert client.delete(f"/api/v1/categories/{gimnasio['id']}", headers=headers).status_code == 200

    september = client.get(
        "/api/v1/budgets/", params={"year": 2026, "month": 9}, headers=headers
    ).json()
    assert len(september) == 1
    assert september[0]["category_id"] is None
    assert september[0]["category_name"] == "Gimnasio Barrio"
    assert september[0]["amount"] == "40.00"
    assert september[0]["spent"] == "35.00"
    assert september[0]["editable"] is False
    assert (
        client.get("/api/v1/budgets/", params={"year": 2026, "month": 10}, headers=headers).json()
        == []
    )

    # (el aviso del 80% de septiembre se generó cuando septiembre era el mes en curso)
    notifications = client.get("/api/v1/notifications/", headers=headers).json()
    assert {n["type"] for n in notifications} == {"budget_category_deleted", "budget_warning"}


# --- Recomendaciones -------------------------------------------------------


def _spend_months(client, headers, account_id, category_id, amounts: dict[str, str]) -> None:
    for posted_at, amount in amounts.items():
        _create_expense(client, headers, account_id, f"-{amount}", posted_at, category_id)


def test_recommendations_flags(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    streaming_id = _find_category(client, headers, "expense", "Suscripciones", "Streaming")
    farmacia_id = _find_category(client, headers, "expense", "Salud", "Farmacia")
    cine_id = _find_category(client, headers, "expense", "Ocio", "Cine/Eventos")

    _spend_months(
        client,
        headers,
        account.id,
        supermercado_id,
        {"2026-07-05": "300.00", "2026-08-05": "320.00", "2026-09-05": "340.00"},
    )
    _spend_months(
        client,
        headers,
        account.id,
        streaming_id,
        {"2026-07-05": "20.00", "2026-08-05": "20.00", "2026-09-05": "20.00"},
    )
    _spend_months(
        client,
        headers,
        account.id,
        farmacia_id,
        {"2026-07-05": "30.00", "2026-08-05": "30.00", "2026-09-05": "30.00"},
    )
    _spend_months(client, headers, account.id, cine_id, {"2026-09-05": "40.00"})
    _create_budget(client, headers, supermercado_id, "250.00")
    _create_budget(client, headers, streaming_id, "21.00")

    recommendations = {
        r["category_id"]: r
        for r in client.get("/api/v1/budgets/recommendations", headers=headers).json()
    }
    assert recommendations[supermercado_id]["flag"] == "raise"
    assert recommendations[supermercado_id]["suggested_amount"] == "320.00"
    assert [m["spent"] for m in recommendations[supermercado_id]["basis"]["months"]] == [
        "300.00",
        "320.00",
        "340.00",
    ]
    assert recommendations[streaming_id]["flag"] == "keep"
    assert recommendations[farmacia_id]["flag"] == "create"
    assert cine_id not in recommendations

    alimentacion_id = _find_category(client, headers, "expense", "Alimentación")
    assert recommendations[alimentacion_id]["basis"]["share_pct"] is not None
    assert recommendations[alimentacion_id]["basis"]["over_typical"] is True
    assert recommendations[supermercado_id]["basis"]["share_pct"] is None


def test_recommendation_same_month_last_year_is_informative(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    category_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    _spend_months(
        client,
        headers,
        account.id,
        category_id,
        {
            "2025-10-05": "900.00",
            "2026-07-05": "100.00",
            "2026-08-05": "100.00",
            "2026-09-05": "100.00",
        },
    )

    [recommendation] = client.get(
        "/api/v1/budgets/recommendations", params={"category_id": category_id}, headers=headers
    ).json()
    assert recommendation["basis"]["same_month_last_year"] == "900.00"
    assert recommendation["suggested_amount"] == "100.00"


# --- Aislamiento -----------------------------------------------------------


def test_budgets_isolated_between_users(client: TestClient, auth_headers) -> None:
    headers_a, _ = auth_headers()
    headers_b, _ = auth_headers()
    category_id = _find_category(client, headers_a, "expense", "Alimentación")
    _create_budget(client, headers_a, category_id, "200.00")

    assert _list(client, headers_b, 2026, 10) == {}
    assert _put(client, headers_b, category_id, "2026-10", "1.00").status_code == 404
    assert (
        client.delete(f"/api/v1/budgets/{category_id}/2026-10", headers=headers_b).status_code
        == 404
    )
    assert _create_budget(client, headers_b, category_id, "50.00").status_code == 201
