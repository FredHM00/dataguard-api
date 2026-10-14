"""Modelo User: identidade, credencial (somente hash) e papel.

A senha em texto puro NUNCA chega a este modelo (hash Argon2 na Etapa 3).
"""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserRole:
    """Papeis validos; o cadastro publico jamais pode escolher ADMIN (Etapa 3)."""

    USER = "user"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN ('user', 'admin')", name="role_values"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=UserRole.USER)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    records: Mapped[list["Record"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan", passive_deletes=True
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship(
        back_populates="actor", passive_deletes=True
    )
