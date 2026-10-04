from fastapi.testclient import TestClient


def test_new_user_has_no_name_or_avatar(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    body = me.json()
    assert body["full_name"] is None
    assert body["has_avatar"] is False


def test_update_full_name(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.patch("/api/v1/users/me/", json={"full_name": "Ana López"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["full_name"] == "Ana López"

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.json()["full_name"] == "Ana López"


def test_full_name_cannot_be_blank(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.patch("/api/v1/users/me/", json={"full_name": "   "}, headers=headers)
    assert response.status_code == 422


def test_upload_view_and_delete_avatar(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    upload = client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("avatar.png", b"\x89PNG\r\n fake png bytes", "image/png")},
    )
    assert upload.status_code == 201
    assert upload.json()["has_avatar"] is True

    view = client.get("/api/v1/users/me/avatar", headers=headers)
    assert view.status_code == 200
    assert view.content == b"\x89PNG\r\n fake png bytes"
    assert view.headers["content-type"] == "image/png"

    deleted = client.delete("/api/v1/users/me/avatar", headers=headers)
    assert deleted.status_code == 204

    view_after = client.get("/api/v1/users/me/avatar", headers=headers)
    assert view_after.status_code == 404

    me = client.get("/api/v1/auth/me", headers=headers)
    assert me.json()["has_avatar"] is False


def test_uploading_new_avatar_replaces_old_one(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("first.png", b"first bytes", "image/png")},
    )
    client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("second.png", b"second bytes", "image/png")},
    )

    view = client.get("/api/v1/users/me/avatar", headers=headers)
    assert view.content == b"second bytes"


def test_avatar_rejects_unsupported_mime_type(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    response = client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("doc.pdf", b"%PDF-1.4", "application/pdf")},
    )
    assert response.status_code == 415


def test_avatar_rejects_oversized_file(client: TestClient, auth_headers) -> None:
    headers, _ = auth_headers()

    big_content = b"0" * (5 * 1024 * 1024 + 1)
    response = client.post(
        "/api/v1/users/me/avatar",
        headers=headers,
        files={"file": ("big.png", big_content, "image/png")},
    )
    assert response.status_code == 413


def test_avatar_is_isolated_between_users(client: TestClient, auth_headers) -> None:
    headers_a, _ = auth_headers()
    headers_b, _ = auth_headers()

    client.post(
        "/api/v1/users/me/avatar",
        headers=headers_a,
        files={"file": ("avatar.png", b"avatar de a", "image/png")},
    )

    view_b = client.get("/api/v1/users/me/avatar", headers=headers_b)
    assert view_b.status_code == 404
