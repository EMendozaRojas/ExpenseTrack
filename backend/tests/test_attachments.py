from fastapi.testclient import TestClient


def _create_transaction(client: TestClient, headers: dict[str, str], account_id: int) -> int:
    response = client.post(
        "/api/v1/transactions/",
        json={
            "account_id": account_id,
            "amount": "-10.00",
            "direction": "expense",
            "posted_at": "2026-03-01",
        },
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_upload_list_download_and_delete_attachment(
    client: TestClient, auth_headers, make_account
) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    transaction_id = _create_transaction(client, headers, account.id)

    upload = client.post(
        f"/api/v1/transactions/{transaction_id}/attachments",
        headers=headers,
        files={"file": ("recibo.png", b"\x89PNG\r\n fake png bytes", "image/png")},
    )
    assert upload.status_code == 201
    body = upload.json()
    assert body["filename"] == "recibo.png"
    assert body["mime_type"] == "image/png"
    assert body["size_bytes"] > 0

    listed = client.get(f"/api/v1/transactions/{transaction_id}/attachments", headers=headers)
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    download = client.get(f"/api/v1/attachments/{body['id']}", headers=headers)
    assert download.status_code == 200
    assert download.content == b"\x89PNG\r\n fake png bytes"
    assert download.headers["content-type"] == "image/png"

    deleted = client.delete(f"/api/v1/attachments/{body['id']}", headers=headers)
    assert deleted.status_code == 204

    listed_after = client.get(f"/api/v1/transactions/{transaction_id}/attachments", headers=headers)
    assert listed_after.json() == []


def test_unsupported_mime_type_rejected(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    transaction_id = _create_transaction(client, headers, account.id)

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/attachments",
        headers=headers,
        files={"file": ("virus.exe", b"MZ...", "application/x-msdownload")},
    )
    assert response.status_code == 415


def test_oversized_file_rejected(client: TestClient, auth_headers, make_account) -> None:
    headers, user = auth_headers()
    account = make_account(user)
    transaction_id = _create_transaction(client, headers, account.id)

    big_content = b"0" * (10 * 1024 * 1024 + 1)
    response = client.post(
        f"/api/v1/transactions/{transaction_id}/attachments",
        headers=headers,
        files={"file": ("grande.png", big_content, "image/png")},
    )
    assert response.status_code == 413


def test_attachment_upload_requires_owned_transaction(
    client: TestClient, auth_headers, make_account
) -> None:
    headers_a, user_a = auth_headers()
    headers_b, _ = auth_headers()
    account_a = make_account(user_a)
    transaction_id = _create_transaction(client, headers_a, account_a.id)

    response = client.post(
        f"/api/v1/transactions/{transaction_id}/attachments",
        headers=headers_b,
        files={"file": ("recibo.png", b"data", "image/png")},
    )
    assert response.status_code == 404


def test_attachment_download_isolated_between_users(
    client: TestClient, auth_headers, make_account
) -> None:
    headers_a, user_a = auth_headers()
    headers_b, _ = auth_headers()
    account_a = make_account(user_a)
    transaction_id = _create_transaction(client, headers_a, account_a.id)

    upload = client.post(
        f"/api/v1/transactions/{transaction_id}/attachments",
        headers=headers_a,
        files={"file": ("recibo.png", b"data", "image/png")},
    ).json()

    response = client.get(f"/api/v1/attachments/{upload['id']}", headers=headers_b)
    assert response.status_code == 404
