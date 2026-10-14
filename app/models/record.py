"""Modelo Record: registro de atendimento com observacoes criptografadas.

O campo notes_ciphertext guarda o token Fernet (base64 ASCII); a descriptografia
so acontece DEPOIS da checagem de autorizacao (Etapa 4).
"""

import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class RecordStatus:
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"


class Record(Base):
    __tablename__ = "records"
    __table_args__ = (
        CheckConstraint(
            "status IN ('open', 'in_progress', 'closed')", name="status_values"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    owner_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    notes_ciphertext: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=RecordStatus.OPEN
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="records")
