"""Regras de cadastro e autenticacao.

- O papel e SEMPRE "user" aqui: nao existe parametro capaz de criar admin.
- Login falho e indistinguivel (401 unico), com hash dummy anti-enumeracao.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateEmail, InvalidCredentials
from app.models.user import User, UserRole
from app.security.passwords import DUMMY_HASH, hash_password, verify_password


def register_user(db: Session, *, email: str, password: str) -> User:
    """Cadastra usuario comum; e-mail duplicado vira DuplicateEmail (409)."""
    clean_email = email.strip().lower()
    exists = db.scalar(select(User).where(User.email == clean_email))
    if exists is not None:
        raise DuplicateEmail(clean_email)
    user = User(
        email=clean_email,
        password_hash=hash_password(password),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate(db: Session, *, email: str, password: str) -> User:
    """Valida credenciais; qualquer falha vira InvalidCredentials (401)."""
    clean_email = email.strip().lower()
    user = db.scalar(select(User).where(User.email == clean_email))
    if user is None:
        verify_password(DUMMY_HASH, password)  # tempo constante, sem efeito
        raise InvalidCredentials()
    if not user.is_active or not verify_password(user.password_hash, password):
        raise InvalidCredentials()
    return user
