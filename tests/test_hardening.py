"""Endurecimento: injecao SQL, entradas malformadas, conta inativa, JWT (Etapa 5)."""

import base64
import json

import jwt
from sqlalchemy import func, select

from app.core.config import settings
from app.models.user import User

PREFIX = "/api/v1"


def _register(client, email, password="segredo-123", raw=None):
    return client.post(f"{PREFIX}/auth/register", json=raw or {"email": email, "password": password})


def _login(client, email, password="segredo-123"):
    return client.post(f"{PREFIX}/auth/login", data={"username": email, "password": password})


def _auth(client, email):
    _register(client, email)
    token = _login(client, email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def test_login_sql_injection_returns_401(client):
    payload = "admin' OR '1'='1"
    response = _login(client, payload, payload)
    assert response.status_code == 401
    assert response.json() == {"detail": "invalid email or password"}


def test_sql_payload_in_record_is_stored_literally(client):
    headers = _auth(client, "sqli@example.com")
    evil = "x'; DROP TABLE users;--"
    response = client.post(
        f"{PREFIX}/records",
        json={"title": evil, "category": "suporte", "notes": "n"},
        headers=headers,
    )
    assert response.status_code == 201
    assert response.json()["title"] == evil
    total = client.db.scalar(select(func.count()).select_from(User))
    assert total >= 1  # tabela users intacta: ORM parametrizou, nada executou


def test_malformed_inputs_rejected_422(client):
    headers = _auth(client, "malformed@example.com")
    assert client.post(
        f"{PREFIX}/records",
        json={"title": "", "category": "c", "notes": "n"},
        headers=headers,
    ).status_code == 422
    assert client.post(
        f"{PREFIX}/records",
        json={"title": "t", "category": "c", "notes": "n" * 10001},
        headers=headers,
    ).status_code == 422
    assert client.get(f"{PREFIX}/records?page=0", headers=headers).status_code == 422
    assert client.get(f"{PREFIX}/records?page_size=0", headers=headers).status_code == 422


def test_inactive_user_is_blocked(client):
    _register(client, "soneca@example.com")
    user = client.db.scalar(select(User).where(User.email == "soneca@example.com"))
    old_token = _login(client, "soneca@example.com").json()["access_token"]
    user.is_active = False
    client.db.commit()
    assert _login(client, "soneca@example.com").status_code == 401
    assert (
        client.get(
            f"{PREFIX}/users/me", headers={"Authorization": f"Bearer {old_token}"}
        ).status_code
        == 401
    )


def test_none_algorithm_token_is_rejected(client):
    _register(client, "alg@example.com")
    token = _login(client, "alg@example.com").json()["access_token"]
    sub = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])["sub"]
    forged = _b64url(json.dumps({"alg": "none", "typ": "JWT"}).encode()) + "." + _b64url(
        json.dumps({"sub": sub}).encode()
    ) + "."
    response = client.get(f"{PREFIX}/users/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_wrong_secret_token_is_rejected(client):
    _register(client, "chave@example.com")
    token = _login(client, "chave@example.com").json()["access_token"]
    sub = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=["HS256"])["sub"]
    forged = jwt.encode({"sub": sub}, "outra-chave-qualquer", algorithm="HS256")
    response = client.get(f"{PREFIX}/users/me", headers={"Authorization": f"Bearer {forged}"})
    assert response.status_code == 401


def test_register_rejects_privilege_fields(client):
    response = _register(client, "x@example.com", raw={"email": "x@example.com", "password": "segredo-123", "is_active": False})
    assert response.status_code == 422
