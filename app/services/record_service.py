"""Regras dos registros: posse, criptografia e auditoria transacional.

- Leitura/escrita exigem ownership (admin e excecao, nao regra).
- Registro alheio ou inexistente: NotFound nos dois casos (sem oraculo).
- notes e cifrado ANTES de persistir e so e decifrado apos o guard passar.
- Listagem dupla: offset (simples, pagina N) e cursor (eficiente em tabelas
  grandes: caminha pelo indice em vez de varrer+descartar com OFFSET).
"""

import base64
import json
from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import Session

from app.audit.logger import log_action
from app.core.exceptions import DecryptionError, NotFound
from app.models.audit_log import AuditAction, AuditResult
from app.models.record import Record
from app.models.user import User, UserRole
from app.security.crypto import decrypt_note, encrypt_note

RESOURCE = "record"
MAX_PAGE_SIZE = 100


def encode_cursor(created_at: datetime, record_id: UUID) -> str:
    """Cursor opaco: posicao (created_at, id), sem nada do dono."""
    payload = json.dumps([created_at.isoformat(), str(record_id)])
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("utf-8")


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    """Valida o cursor; qualquer adulteracao vira ValueError (rota: 422)."""
    try:
        created_raw, id_raw = json.loads(
            base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8")
        )
        return datetime.fromisoformat(created_raw), UUID(id_raw)
    except (ValueError, TypeError, KeyError):
        raise ValueError("invalid cursor") from None


def _owned_record(db: Session, *, record_id: UUID, requester: User) -> Record:
    """Busca com guard de posse; alheio ou inexistente = NotFound."""
    record = db.get(Record, record_id)
    if record is None:
        raise NotFound()
    if requester.role != UserRole.ADMIN and record.owner_id != requester.id:
        log_action(
            db,
            actor_id=requester.id,
            action=AuditAction.RECORD_READ,
            resource_type=RESOURCE,
            resource_id=str(record_id),
            result=AuditResult.DENIED,
        )
        db.commit()  # persiste so o log: a operacao em si nao fez nada
        raise NotFound()
    return record


def _to_read(record: Record) -> dict:
    """Monta a resposta descriptografando apos o guard (pode levantar 500)."""
    try:
        notes = decrypt_note(record.notes_ciphertext)
    except DecryptionError:
        raise
    return {
        "id": record.id,
        "title": record.title,
        "category": record.category,
        "notes": notes,
        "status": record.status,
        "created_at": record.created_at,
        "updated_at": record.updated_at,
    }


def create_record(
    db: Session, *, owner: User, title: str, category: str, notes: str
) -> dict:
    """Cria com notes cifrado + log, tudo num commit so."""
    record = Record(
        owner_id=owner.id,
        title=title.strip(),
        category=category.strip(),
        notes_ciphertext=encrypt_note(notes),
    )
    db.add(record)
    db.flush()
    log_action(
        db,
        actor_id=owner.id,
        action=AuditAction.RECORD_CREATE,
        resource_type=RESOURCE,
        resource_id=str(record.id),
    )
    db.commit()
    db.refresh(record)
    return _to_read(record)


def list_records(
    db: Session, *, requester: User, page: int, page_size: int
) -> tuple[list[dict], int]:
    """Pagina os autorizados: todos (admin) ou so os proprios."""
    size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * size
    statement = select(Record).order_by(Record.created_at.desc(), Record.id.desc())
    count_stmt = select(func.count()).select_from(Record)
    if requester.role != UserRole.ADMIN:
        statement = statement.where(Record.owner_id == requester.id)
        count_stmt = count_stmt.where(Record.owner_id == requester.id)
    total = db.scalar(count_stmt) or 0
    records = db.scalars(statement.offset(offset).limit(size)).all()
    return [_to_read(record) for record in records], total


def list_records_cursor(
    db: Session, *, requester: User, cursor: str | None, limit: int
) -> tuple[list[dict], str | None]:
    """Pagina por chave: eficiente em tabelas grandes (usa o indice).

    Ordenacao estavel (created_at DESC, id DESC); o cursor marca a posicao
    do ultimo item. Comparacao de tupla no Postgres, filtro de posse igual.
    """
    size = min(limit, MAX_PAGE_SIZE)
    statement = select(Record).order_by(Record.created_at.desc(), Record.id.desc())
    if requester.role != UserRole.ADMIN:
        statement = statement.where(Record.owner_id == requester.id)
    if cursor is not None:
        cursor_created, cursor_id = decode_cursor(cursor)
        statement = statement.where(
            tuple_(Record.created_at, Record.id) < (cursor_created, cursor_id)
        )
    records = db.scalars(statement.limit(size + 1)).all()
    page = records[:size]
    items = [_to_read(record) for record in page]
    next_cursor = (
        encode_cursor(items[-1]["created_at"], items[-1]["id"])
        if len(records) > size
        else None
    )
    return items, next_cursor


def get_record(db: Session, *, record_id: UUID, requester: User) -> dict:
    """Leitura individual (nao auditada: evita trilha de quem leu o que)."""
    return _to_read(_owned_record(db, record_id=record_id, requester=requester))


def update_record(
    db: Session,
    *,
    record_id: UUID,
    requester: User,
    title: str | None,
    category: str | None,
    notes: str | None,
    status: str | None,
) -> dict:
    """Atualizacao parcial com guard + re-cifragem se notes mudar + log."""
    record = _owned_record(db, record_id=record_id, requester=requester)
    if title is not None:
        record.title = title.strip()
    if category is not None:
        record.category = category.strip()
    if notes is not None:
        record.notes_ciphertext = encrypt_note(notes)
    if status is not None:
        record.status = status
    log_action(
        db,
        actor_id=requester.id,
        action=AuditAction.RECORD_UPDATE,
        resource_type=RESOURCE,
        resource_id=str(record.id),
    )
    db.commit()
    db.refresh(record)
    return _to_read(record)


def delete_record(db: Session, *, record_id: UUID, requester: User) -> None:
    """Remocao com guard + log (o log referencia um id que deixa de existir)."""
    record = _owned_record(db, record_id=record_id, requester=requester)
    log_action(
        db,
        actor_id=requester.id,
        action=AuditAction.RECORD_DELETE,
        resource_type=RESOURCE,
        resource_id=str(record.id),
    )
    db.delete(record)
    db.commit()
