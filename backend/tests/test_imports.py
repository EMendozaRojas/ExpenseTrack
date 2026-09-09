from fastapi.testclient import TestClient


def _find_category(
    client: TestClient, headers: dict[str, str], kind: str, root_name: str, sub_name: str
) -> int:
    roots = client.get("/api/v1/categories/", params={"kind": kind}, headers=headers).json()
    root = next(r for r in roots if r["name"] == root_name)
    sub = next(c for c in root["children"] if c["name"] == sub_name)
    return sub["id"]


def _upload(
    client: TestClient, headers: dict[str, str], account_id: int, csv_text: str, filename: str = "extracto.csv"
):
    return client.post(
        "/api/v1/imports/",
        headers=headers,
        data={"account_id": str(account_id)},
        files={"file": (filename, csv_text.encode("utf-8"), "text/csv")},
    )


BASIC_CSV = (
    "Fecha;Concepto;Importe\n"
    "2026-03-01;COMPRA EN MERCADONA 1234;-42,50\n"
    "2026-03-02;PAGO EN AMAZON;-19,99\n"
    "2026-03-03;NOMINA EMPRESA;1500,00\n"
)


def test_upload_previews_all_as_new(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = _upload(client, headers, account.id, BASIC_CSV)
    assert response.status_code == 201
    body = response.json()
    assert body["new_count"] == 3
    assert body["exact_duplicate_count"] == 0
    assert body["probable_duplicate_count"] == 0
    assert body["range_start"] == "2026-03-01"
    assert body["range_end"] == "2026-03-03"
    assert len(body["rows"]) == 3


def test_unsupported_extension_rejected(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = _upload(client, headers, account.id, BASIC_CSV, filename="extracto.pdf")
    assert response.status_code == 415


def test_unrecognized_columns_rejected(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    response = _upload(client, headers, account.id, "colA;colB\n1;2\n")
    assert response.status_code == 422


def test_commit_append_new_creates_categorized_transactions(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")
    sin_clasificar_id = _find_category(
        client, headers, "expense", "Finanzas y Otros", "Sin Clasificar"
    )

    preview = _upload(client, headers, account.id, BASIC_CSV).json()
    commit = client.post(
        f"/api/v1/imports/{preview['id']}/commit",
        json={"strategy": "append_new"},
        headers=headers,
    )
    assert commit.status_code == 200
    body = commit.json()
    assert body["inserted_count"] == 3
    assert body["skipped_count"] == 0

    items = client.get("/api/v1/transactions/", headers=headers).json()["items"]
    by_desc = {tx["raw_description"]: tx for tx in items}
    assert by_desc["COMPRA EN MERCADONA 1234"]["category_id"] == supermercado_id
    assert by_desc["COMPRA EN MERCADONA 1234"]["source"] == "import"
    assert by_desc["PAGO EN AMAZON"]["category_id"] == sin_clasificar_id
    assert by_desc["NOMINA EMPRESA"]["direction"] == "income"


def test_commit_twice_rejected(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    preview = _upload(client, headers, account.id, BASIC_CSV).json()

    first = client.post(
        f"/api/v1/imports/{preview['id']}/commit", json={"strategy": "append_new"}, headers=headers
    )
    assert first.status_code == 200

    second = client.post(
        f"/api/v1/imports/{preview['id']}/commit", json={"strategy": "append_new"}, headers=headers
    )
    assert second.status_code == 409


def test_reupload_same_file_detects_exact_duplicates(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    first_preview = _upload(client, headers, account.id, BASIC_CSV).json()
    client.post(
        f"/api/v1/imports/{first_preview['id']}/commit",
        json={"strategy": "append_new"},
        headers=headers,
    )

    second_preview = _upload(client, headers, account.id, BASIC_CSV).json()
    assert second_preview["new_count"] == 0
    assert second_preview["exact_duplicate_count"] == 3

    commit = client.post(
        f"/api/v1/imports/{second_preview['id']}/commit",
        json={"strategy": "append_new"},
        headers=headers,
    )
    assert commit.json()["inserted_count"] == 0
    assert commit.json()["skipped_count"] == 3


def test_probable_duplicate_detected_for_similar_row(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)

    original = "Fecha;Concepto;Importe\n2026-03-01;COMPRA EN MERCADONA MADRID CENTRO;-42,50\n"
    preview1 = _upload(client, headers, account.id, original).json()
    client.post(
        f"/api/v1/imports/{preview1['id']}/commit", json={"strategy": "append_new"}, headers=headers
    )

    # mismo importe, un día después, texto ligeramente distinto (banco reformateó el extracto)
    similar = "Fecha;Concepto;Importe\n2026-03-02;COMPRA MERCADONA MADRID CENTRO;-42,50\n"
    preview2 = _upload(client, headers, account.id, similar).json()
    assert preview2["probable_duplicate_count"] == 1
    assert preview2["rows"][0]["classification"] == "PROBABLE_DUPLICATE"
    assert preview2["rows"][0]["matched_transaction_id"] is not None


def test_replace_range_soft_deletes_import_rows_but_keeps_manual(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    supermercado_id = _find_category(client, headers, "expense", "Alimentación", "Supermercado")

    # movimiento manual dentro del rango: no debe tocarse nunca
    manual = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account.id,
            "amount": "-5.00",
            "direction": "expense",
            "posted_at": "2026-03-02",
            "category_id": supermercado_id,
            "note": "Efectivo",
        },
        headers=headers,
    ).json()

    partial_csv = "Fecha;Concepto;Importe\n2026-03-01;COMPRA EN MERCADONA 1234;-42,50\n"
    preview1 = _upload(client, headers, account.id, partial_csv).json()
    client.post(
        f"/api/v1/imports/{preview1['id']}/commit", json={"strategy": "append_new"}, headers=headers
    )

    full_csv = (
        "Fecha;Concepto;Importe\n"
        "2026-03-01;COMPRA EN MERCADONA 1234;-42,50\n"
        "2026-03-03;PAGO EN AMAZON;-19,99\n"
    )
    preview2 = _upload(client, headers, account.id, full_csv).json()
    commit2 = client.post(
        f"/api/v1/imports/{preview2['id']}/commit",
        json={"strategy": "replace_range"},
        headers=headers,
    )
    body = commit2.json()
    assert body["replaced_count"] == 1
    assert body["inserted_count"] == 2

    items = client.get(
        "/api/v1/transactions/",
        params={"date_from": "2026-03-01", "date_to": "2026-03-03"},
        headers=headers,
    ).json()["items"]
    descriptions = {tx["raw_description"] or tx["note"] for tx in items}
    assert "COMPRA EN MERCADONA 1234" in descriptions
    assert "PAGO EN AMAZON" in descriptions
    assert "Efectivo" in descriptions
    assert any(tx["id"] == manual["id"] for tx in items)


def test_import_isolated_between_users(client: TestClient, auth_headers, make_account) -> None:
    headers_a, user_a = auth_headers()
    _, user_b = auth_headers()
    account_b = make_account(user_b)

    response = _upload(client, headers_a, account_b.id, BASIC_CSV)
    assert response.status_code == 404
