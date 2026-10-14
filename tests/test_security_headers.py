"""Cabecalhos de seguranca presentes em respostas publicas e privadas (Etapa 11)."""

PREFIX = "/api/v1"


def _auth(client, email):
    client.post(f"{PREFIX}/auth/register", json={"email": email, "password": "segredo-123"})
    token = client.post(
        f"{PREFIX}/auth/login", data={"username": email, "password": "segredo-123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_public_responses_carry_security_headers(client):
    response = client.get("/health")
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_private_responses_carry_security_headers(client):
    headers = _auth(client, "headers@example.com")
    response = client.get(f"{PREFIX}/records", headers=headers)
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_not_found_responses_carry_security_headers(client):
    response = client.get("/rota-que-nao-existe")
    assert response.status_code == 404
    assert response.headers["Cache-Control"] == "no-store"
