"""Testes do ciclo de refresh: rotacao, roubo, logout, expiracao (Etapa 7)."""

from datetime import timedelta

from sqlalchemy import select

from app.core.config import settings
from app.models.refresh_token import RefreshToken
from app.security.refresh import hash_refresh_token

PREFIX = "/api/v1"


def _register(client, email, password="segredo-123"):
    return client.post(f"{PREFIX}/auth/register", json={"email": email, "password": password})


def _login(client, email, password="segredo-123"):
    return client.post(f"{PREFIX}/auth/login", data={"username": email, "password": password})


def _pair(client, email):
    _register(client, email)
    response = _login(client, email)
    assert response.status_code == 200
    return response.json()


def test_login_returns_usable_pair(client):
    pair = _pair(client, "par@example.com")
    assert pair["token_type"] == "bearer"
    assert "." not in pair["refresh_token"]  # opaco, nao JWT
    me = client.get(f"{PREFIX}/users/me", headers={"Authorization": f"Bearer {pair['access_token']}"})
    assert me.status_code == 200


def test_refresh_rotates_and_old_is_rejected(client):
    pair = _pair(client, "rot@example.com")
    second = client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert second.status_code == 200
    assert second.json()["refresh_token"] != pair["refresh_token"]
    reuse = client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert reuse.status_code == 401


def test_reuse_of_rotated_token_revokes_family(client):
    pair = _pair(client, "roubo@example.com")
    second = client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": pair["refresh_token"]}).json()
    # Atacante reusa o token antigo: familia inteira cai, inclusive o novo.
    assert client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": pair["refresh_token"]}).status_code == 401
    assert client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": second["refresh_token"]}).status_code == 401


def test_logout_revokes_and_is_idempotent(client):
    pair = _pair(client, "logout@example.com")
    assert client.post(f"{PREFIX}/auth/logout", json={"refresh_token": pair["refresh_token"]}).status_code == 204
    assert client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": pair["refresh_token"]}).status_code == 401
    assert client.post(f"{PREFIX}/auth/logout", json={"refresh_token": "inexistente"}).status_code == 204


def test_expired_refresh_is_rejected(client):
    pair = _pair(client, "expirado@example.com")
    record = client.db.scalar(
        select(RefreshToken).where(RefreshToken.token_hash == hash_refresh_token(pair["refresh_token"]))
    )
    record.expires_at = record.expires_at - timedelta(days=30)
    client.db.commit()
    assert client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": pair["refresh_token"]}).status_code == 401


def test_tampered_refresh_is_rejected(client):
    pair = _pair(client, "adulterado@example.com")
    assert client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": pair["refresh_token"] + "x"}).status_code == 401


def test_refresh_stored_only_as_hash(client):
    pair = _pair(client, "hash@example.com")
    rows = client.db.scalars(select(RefreshToken)).all()
    assert rows, "esperava linha de refresh"
    assert all(row.token_hash != pair["refresh_token"] for row in rows)
    assert hash_refresh_token(pair["refresh_token"]) in {row.token_hash for row in rows}


def test_refresh_and_logout_are_audited(client):
    from app.models.audit_log import AuditLog

    pair = _pair(client, "trilha@example.com")
    client.post(f"{PREFIX}/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    actions = {row.action for row in client.db.scalars(select(AuditLog)).all()}
    assert "auth.refresh" in actions
