"""Escrita da trilha de auditoria.

log_action so adiciona (flush); o commit e do chamador, na mesma transacao
da operacao auditada. O que entra aqui: quem, o-que, resultado, quando.
O que NUNCA entra: senhas, tokens, observacoes em texto puro.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditAction, AuditLog, AuditResult


def log_action(
    db: Session,
    *,
    actor_id: UUID | None,
    action: str = AuditAction.RECORD_CREATE,
    resource_type: str | None = None,
    resource_id: str | None = None,
    result: str = AuditResult.SUCCESS,
) -> AuditLog:
    """Enfileira um AuditLog na transacao corrente (sem commit)."""
    entry = AuditLog(
        actor_id=actor_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        result=result,
    )
    db.add(entry)
    db.flush()
    return entry
