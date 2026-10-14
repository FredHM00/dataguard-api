"""Emissao, rotacao e revogacao de refresh tokens.

- issue_pair: login/pos-refresh; grava so o hash.
- rotate: troca o refresh por um novo; reutilizar um ja trocado = roubo
  (revoga a familia inteira do usuario).
- revoke: logout idempotente (token desconhecido tambem da 204).
"""

from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.audit.logger import log_action
from app.core.config import settings
from app.core.exceptions import InvalidToken
from app.models.audit_log import AuditAction, AuditResult
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.security.refresh import generate_refresh_token, hash_refresh_token
from app.security.tokens import TOKEN_TYPE, create_access_token


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def issue_pair(db: Session, user: User) -> dict[str, str]:
    """Cria access + refresh para o usuario (login ou pos-rotacao)."""
    plain = generate_refresh_token()
    db.add(
        RefreshToken(
            user_id=user.id,
            token_hash=hash_refresh_token(plain),
            expires_at=_utcnow() + settings.refresh_expires,
        )
    )
    db.commit()
    return {
        "access_token": create_access_token(user.id),
        "refresh_token": plain,
        "token_type": TOKEN_TYPE,
    }


def rotate(db: Session, presented: str) -> dict[str, str]:
    """Troca um refresh valido por um par novo (uso unico)."""
    record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(presented)
        )
    )
    if record is None:
        raise InvalidToken()
    user = db.get(User, record.user_id)
    if (
        user is None
        or not user.is_active
        or record.expires_at.replace(tzinfo=timezone.utc) <= _utcnow()
    ):
        if record.revoked_at is None:
            record.revoked_at = _utcnow()
            db.commit()
        raise InvalidToken()
    if record.revoked_at is not None:
        # Reutilizacao de token ja rotacionado: possivel roubo.
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == record.user_id)
            .values(revoked_at=_utcnow())
        )
        log_action(
            db,
            actor_id=record.user_id,
            action=AuditAction.AUTH_REFRESH,
            result=AuditResult.DENIED,
        )
        db.commit()
        raise InvalidToken()
    record.revoked_at = _utcnow()
    db.commit()
    log_action(db, actor_id=user.id, action=AuditAction.AUTH_REFRESH)
    return issue_pair(db, user)


def revoke(db: Session, presented: str) -> None:
    """Logout: revoga se existir; desconhecido tambem termina em 204."""
    record = db.scalar(
        select(RefreshToken).where(
            RefreshToken.token_hash == hash_refresh_token(presented)
        )
    )
    if record is not None and record.revoked_at is None:
        record.revoked_at = _utcnow()
        log_action(db, actor_id=record.user_id, action=AuditAction.AUTH_LOGOUT)
    db.commit()
