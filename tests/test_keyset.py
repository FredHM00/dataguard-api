"""Paginacao por cursor: ordem estavel, fim e isolamento (Etapa 10)."""

PREFIX = "/api/v1"


def _auth(client, email):
    client.post(f"{PREFIX}/auth/register", json={"email": email, "password": "segredo-123"})
    token = client.post(
        f"{PREFIX}/auth/login", data={"username": email, "password": "segredo-123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _seed(client, headers, count, prefix="k"):
    for index in range(count):
        client.post(
            f"{PREFIX}/records",
            json={"title": f"{prefix}{index}", "category": "c", "notes": "n"},
            headers=headers,
        )


def test_cursor_walks_all_pages_without_overlap(client):
    headers = _auth(client, "cursor@example.com")
    _seed(client, headers, 5)
    seen, cursor = [], None
    for _ in range(4):
        params = {"limit": 2}
        if cursor:
            params["cursor"] = cursor
        page = client.get(f"{PREFIX}/records/cursor", params=params, headers=headers).json()
        seen.extend(item["title"] for item in page["items"])
        cursor = page["next_cursor"]
        if cursor is None:
            break
    assert sorted(seen) == ["k0", "k1", "k2", "k3", "k4"]
    assert cursor is None  # fim: sem proxima pagina


def test_cursor_limit_capped_at_100(client):
    headers = _auth(client, "teto@example.com")
    assert client.get(f"{PREFIX}/records/cursor?limit=101", headers=headers).status_code == 422


def test_tampered_cursor_returns_422(client):
    headers = _auth(client, "sujo@example.com")
    assert client.get(f"{PREFIX}/records/cursor?cursor=lixo!", headers=headers).status_code == 422


def test_cursor_respects_ownership(client):
    headers_a = _auth(client, "dona@example.com")
    headers_b = _auth(client, "outro@example.com")
    _seed(client, headers_a, 2, prefix="a")
    _seed(client, headers_b, 1, prefix="b")
    page = client.get(f"{PREFIX}/records/cursor", headers=headers_b).json()
    assert [item["title"] for item in page["items"]] == ["b0"]
    assert page["next_cursor"] is None
