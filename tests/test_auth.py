"""Controles de autenticacao e autorizacao (Etapa 3)."""

from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings

PREFIX = "/api/v1"


def _register(client, email="ana@example.com", password="segredo-123", extra=None):
    body = {"email": email, "password": password}
    if extra:
        body.update(extra)
    return client.post(f"{PREFIX}/auth/register", json=body)


def _login(client, email="ana@example.com", password="segredo-123"):
    return client.post(
        f"{PREFIX}/auth/login", data={"username": email, "password": password}
    )


def test_register_returns_201_and_public_shape(client):
    response = _register(client)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "ana@example.com"
    assert data["role"] == "user"
    assert data["is_active"] is True
    assert "password_hash" not in data
    assert "password" not in data


def test_register_duplicate_email_returns_409(client):
    assert _register(client, email="dup@example.com").status_code == 201
    response = _register(client, email="dup@example.com")
    assert response.status_code == 409


def test_register_with_role_is_rejected_422(client):
    response = _register(client, email="esperto@example.com", extra={"role": "admin"})
    assert response.status_code == 422


def test_register_with_short_password_is_rejected_422(client):
    response = _register(client, email="curta@example.com", password="abc")
    assert response.status_code == 422


def test_login_returns_bearer_token(client):
    _register(client)
    response = _login(client)
    assert response.status_code == 200
    data = response.json()
    assert data["token_type"] == "bearer"
    assert len(data["access_token"].split(".")) == 3  # header.payload.signature


def test_login_wrong_password_returns_401(client):
    _register(client)
    response = _login(client, password="errada-999")
    assert response.status_code == 401
    assert response.json() == {"detail": "invalid email or password"}


def test_login_unknown_email_returns_same_401(client):
    response = _login(client, email="ninguem@example.com")
    assert response.status_code == 401
    assert response.json() == {"detail": "invalid email or password"}


def test_me_without_token_returns_401(client):
    assert client.get(f"{PREFIX}/users/me").status_code == 401


def test_me_with_token_returns_profile(client):
    _register(client)
    token = _login(client).json()["access_token"]
    response = client.get(
        f"{PREFIX}/users/me", headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "ana@example.com"


def test_me_with_tampered_token_returns_401(client):
    _register(client)
    token = _login(client).json()["access_token"]
    tampered = token[:-2] + ("aa" if not token.endswith("aa") else "bb")
    response = client.get(
        f"{PREFIX}/users/me", headers={"Authorization": f"Bearer {tampered}"}
    )
    assert response.status_code == 401


def test_me_with_expired_token_returns_401(client):
    _register(client)
    token = _login(client).json()["access_token"]
    user_id = jwt.decode(
        token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
    )["sub"]
    expired = jwt.encode(
        {
            "sub": user_id,
            "exp": datetime.now(timezone.utc) - timedelta(minutes=1),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    response = client.get(
        f"{PREFIX}/users/me", headers={"Authorization": f"Bearer {expired}"}
    )
    assert response.status_code == 401


def test_login_rate_limit_blocks_abuse(client):
    _register(client, email="alvo-rl@example.com")
    statuses = [
        client.post(
            f"{PREFIX}/auth/login",
            data={"username": "alvo-rl@example.com", "password": "segredo-123"},
        ).status_code
        for _ in range(11)
    ]
    assert statuses[:10] == [200] * 10
    assert statuses[10] == 429


def test_password_is_hashed_in_database(client):
    _register(client, email="hash@example.com", password="segredo-123")
    from sqlalchemy import select

    from app.models.user import User

    stored = client.db.scalar(
        select(User.password_hash).where(User.email == "hash@example.com")
    )
    assert stored != "segredo-123"
    assert stored.startswith("$argon2")
