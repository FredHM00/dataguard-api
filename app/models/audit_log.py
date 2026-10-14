"""Modelo AuditLog: trilha de auditoria SEM conteudo sensivel.

Regra de ouro: aqui moram quem/o-que/resultado/quando. Senhas, tokens e
observacoes descriptografadas NUNCA entram nesta tabela.
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AuditAction:
    AUTH_REGISTER = "auth.register"
    AUTH_LOGIN = "auth.login"
    AUTH_REFRESH = "auth.refresh"
    AUTH_LOGOUT = "auth.logout"
    RECORD_CREATE = "record.create"
    RECORD_READ = "record.read"
    RECORD_UPDATE = "record.update"
    RECORD_DELETE = "record.delete"
    AUDIT_READ = "audit.read"


class AuditResult:
    SUCCESS = "success"
    FAILURE = "failure"
    DENIED = "denied"


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (
        CheckConstraint(
            "result IN ('success', 'failure', 'denied')", name="result_values"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Anulavel + SET NULL: o log sobrevive a remocao do usuario.
    actor_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    resource_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    result: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), index=True
    )

    actor: Mapped["User | None"] = relationship(back_populates="audit_logs")
