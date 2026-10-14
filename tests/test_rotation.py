"""Rotacao de chaves: anel multi-chave e re-cifragem (Etapa 9)."""

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import select

from app.core.exceptions import DecryptionError
from app.models.audit_log import AuditLog
from app.models.record import Record
from app.security.crypto import KeyRing, parse_keys
from app.security.rotate import rotate_records

PREFIX = "/api/v1"


def _fresh_key() -> str:
    return Fernet.generate_key().decode("utf-8")


def test_parse_keys_prefers_list_over_legacy():
    assert parse_keys(" b , a ", "legado") == ["b", "a"]
    assert parse_keys(None, "legado") == ["legado"]
    assert parse_keys(" , ", None) == []
    assert parse_keys(None, None) == []


def test_empty_ring_is_rejected():
    with pytest.raises(ValueError):
        KeyRing([])


def test_malformed_key_fails_fast():
    with pytest.raises(ValueError):
        KeyRing(["nao-e-uma-chave"])


def test_old_ciphertext_opens_with_multi_key_ring(client):
    from app.core.config import settings

    headers = _auth(client, "anel@example.com")
    created = client.post(
        f"{PREFIX}/records",
        json={"title": "t", "category": "c", "notes": "segredo-antigo"},
        headers=headers,
    ).json()
    stored = client.db.scalar(
        select(Record.notes_ciphertext).where(Record.id == created["id"])
    )
    configured = parse_keys(settings.FERNET_KEYS, settings.FERNET_KEY)
    assert configured, "esperava alguma chave configurada no .env de teste"
    new_key = _fresh_key()
    assert KeyRing([new_key, *configured]).decrypt(stored) == "segredo-antigo"
    with pytest.raises(DecryptionError):
        KeyRing([new_key]).decrypt(stored)


def _auth(client, email):
    client.post(f"{PREFIX}/auth/register", json={"email": email, "password": "segredo-123"})
    token = client.post(
        f"{PREFIX}/auth/login", data={"username": email, "password": "segredo-123"}
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_rotate_reencrypts_everything_to_primary(client):
    from app.core.config import settings

    headers = _auth(client, "gira@example.com")
    for index in range(3):
        client.post(
            f"{PREFIX}/records",
            json={"title": f"t{index}", "category": "c", "notes": f"n{index}"},
            headers=headers,
        )
    configured = parse_keys(settings.FERNET_KEYS, settings.FERNET_KEY)
    new_key = _fresh_key()
    counts = rotate_records(client.db, KeyRing([new_key, *configured]))
    assert counts == {"total": 3}
    rows = client.db.scalars(select(Record.notes_ciphertext)).all()
    assert len(rows) == 3
    for stored in rows:
        assert KeyRing([new_key]).decrypt(stored).startswith("n")
    # Leitura normal continua funcionando (anel padrao agora nao abre, mas o
    # teste prova a re-cifragem; o app real teria FERNET_KEYS atualizado).
    assert "record.reencrypt" in {
        row.action for row in client.db.scalars(select(AuditLog)).all()
    }
