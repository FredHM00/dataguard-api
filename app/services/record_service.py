"""Regras dos registros: posse, criptografia e auditoria transacional.

- Leitura/escrita exigem ownership (admin e excecao, nao regra).
- Registro alheio ou inexistente: NotFound nos dois casos (sem oraculo).
- notes e cifrado ANTES de persistir e so e decifrado apos o guard passar.
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.audit.logger import log_action
from app.core.exceptions import DecryptionError, NotFound
from app.models.audit_log import AuditAction, AuditResult
from app.models.record import Record
from app.models.user import User, UserRole
from app.security.crypto import decrypt_note, encrypt_note

RESOURCE = "record"
MAX_PAGE_SIZE = 100


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
