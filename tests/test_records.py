"""Registros protegidos: posse, criptografia em repouso, auditoria (Etapa 4)."""

from sqlalchemy import select
from fastapi.testclient import TestClient

from app.models.audit_log import AuditLog
from app.models.record import Record
from app.models.user import User, UserRole
from app.security.crypto import decrypt_note
from app.security.passwords import hash_password

PREFIX = "/api/v1"


def _register(client: TestClient, email: str, password: str = "segredo-123"):
    return client.post(
        f"{PREFIX}/auth/register", json={"email": email, "password": password}
    )


def _login(client: TestClient, email: str, password: str = "segredo-123") -> str:
    response = client.post(
        f"{PREFIX}/auth/login", data={"username": email, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth(client: TestClient, email: str) -> dict[str, str]:
    _register(client, email)
    return {"Authorization": f"Bearer {_login(client, email)}"}


def _make_admin(client: TestClient, email: str = "admin@example.com") -> dict[str, str]:
    client.db.add(
        User(
            email=email,
            password_hash=hash_password("admin-123"),
            role=UserRole.ADMIN,
            is_active=True,
        )
    )
    client.db.commit()
    return {"Authorization": f"Bearer {_login(client, email, 'admin-123')}"}


def _create(client: TestClient, headers, title="Primeiro atendimento", notes="telefone 9999-0000"):
    return client.post(
        f"{PREFIX}/records",
        json={"title": title, "category": "suporte", "notes": notes},
        headers=headers,
    )


def test_create_returns_201_with_plaintext_for_owner(client: TestClient):
    headers = _auth(client, "ana@example.com")
    response = _create(client, headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Primeiro atendimento"
    assert data["notes"] == "telefone 9999-0000"
    assert data["status"] == "open"
    assert "notes_ciphertext" not in data


def test_notes_are_encrypted_at_rest(client: TestClient):
    headers = _auth(client, "cripto@example.com")
    created = _create(client, headers, notes="dado ultra-sensivel").json()
    stored = client.db.scalar(
        select(Record.notes_ciphertext).where(Record.id == created["id"])
    )
    assert stored != "dado ultra-sensivel"
    assert "ultra-sensivel" not in stored
    assert decrypt_note(stored) == "dado ultra-sensivel"


def test_list_is_scoped_to_owner(client: TestClient):
    headers_a = _auth(client, "a@example.com")
    headers_b = _auth(client, "b@example.com")
    _create(client, headers_a, title="a1")
    _create(client, headers_a, title="a2")
    _create(client, headers_b, title="b1")
    data = client.get(f"{PREFIX}/records", headers=headers_a).json()
    assert data["total"] == 2
    assert {item["title"] for item in data["items"]} == {"a1", "a2"}


def test_other_users_record_returns_404_not_403(client: TestClient):
    headers_a = _auth(client, "alvo@example.com")
    headers_b = _auth(client, "intruso@example.com")
    record_id = _create(client, headers_a).json()["id"]
    for method in ("get", "patch", "delete"):
        call = getattr(client, method)
        kwargs = {"headers": headers_b}
        if method == "patch":
            kwargs["json"] = {"title": "invadido"}
        assert call(f"{PREFIX}/records/{record_id}", **kwargs).status_code == 404
    # Nada mudou para o dono.
    intact = client.get(f"{PREFIX}/records/{record_id}", headers=headers_a).json()
    assert intact["title"] == "Primeiro atendimento"


def test_denied_attempt_is_audited(client: TestClient):
    headers_a = _auth(client, "vitima@example.com")
    headers_b = _auth(client, "bisbilhoteiro@example.com")
    record_id = _create(client, headers_a).json()["id"]
    client.get(f"{PREFIX}/records/{record_id}", headers=headers_b)
    denied = client.db.scalar(
        select(AuditLog).where(AuditLog.result == "denied")
    )
    assert denied is not None
    assert denied.resource_id == record_id


def test_malformed_uuid_returns_422(client: TestClient):
    headers = _auth(client, "uuid@example.com")
    assert client.get(f"{PREFIX}/records/nao-e-uuid", headers=headers).status_code == 422


def test_pagination_caps_and_counts(client: TestClient):
    headers = _auth(client, "pag@example.com")
    for index in range(3):
        _create(client, headers, title=f"r{index}")
    page1 = client.get(f"{PREFIX}/records?page=1&page_size=2", headers=headers).json()
    assert page1["total"] == 3
    assert len(page1["items"]) == 2
    page2 = client.get(f"{PREFIX}/records?page=2&page_size=2", headers=headers).json()
    assert len(page2["items"]) == 1
    assert client.get(f"{PREFIX}/records?page_size=101", headers=headers).status_code == 422


def test_update_and_delete_flow(client: TestClient):
    headers = _auth(client, "fluxo@example.com")
    record_id = _create(client, headers).json()["id"]
    updated = client.patch(
        f"{PREFIX}/records/{record_id}",
        json={"status": "closed", "notes": "atualizado"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "closed"
    assert updated.json()["notes"] == "atualizado"
    assert client.patch(
        f"{PREFIX}/records/{record_id}", json={"status": "bogus"}, headers=headers
    ).status_code == 422
    assert client.delete(f"{PREFIX}/records/{record_id}", headers=headers).status_code == 204
    assert client.get(f"{PREFIX}/records/{record_id}", headers=headers).status_code == 404


def test_audit_log_restricted_to_admin(client: TestClient):
    user_headers = _auth(client, "comum@example.com")
    admin_headers = _make_admin(client)
    _create(client, user_headers)
    assert client.get(f"{PREFIX}/audit-logs", headers=user_headers).status_code == 403
    assert client.get(f"{PREFIX}/audit-logs").status_code == 401
    response = client.get(f"{PREFIX}/audit-logs", headers=admin_headers)
    assert response.status_code == 200
    actions = {entry["action"] for entry in response.json()["items"]}
    assert "record.create" in actions
    assert "audit.read" not in actions  # o log da propria leitura entra depois


def test_audit_contains_no_secrets(client: TestClient):
    headers = _auth(client, "sigilo@example.com")
    _create(client, headers, notes="segredo-absoluto-123")
    rows = client.db.scalars(select(AuditLog)).all()
    assert rows, "esperava linhas de auditoria"
    blob = " ".join(
        f"{row.action} {row.resource_type} {row.resource_id} {row.result}" for row in rows
    )
    assert "segredo-absoluto-123" not in blob
    assert "segredo-123" not in blob


def test_unauthenticated_record_access_returns_401(client: TestClient):
    assert client.get(f"{PREFIX}/records").status_code == 401
    assert client.post(f"{PREFIX}/records", json={}).status_code in (401, 422)
