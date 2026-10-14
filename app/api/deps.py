"""Dependencias de autenticacao/autorizacao (guards das rotas)."""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core.exceptions import InvalidToken
from app.db.session import get_db
from app.models.user import User, UserRole
from app.security.tokens import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def _unauthorized(detail: str) -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_current_user(
    db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)
) -> User:
    """Valida o JWT e devolve o dono dele; inativo ou inexistente = 401."""
    try:
        user_id = decode_access_token(token)
    except InvalidToken:
        raise _unauthorized("invalid or expired token") from None
    user = db.get(User, user_id)
    if user is None or not user.is_active:
        raise _unauthorized("invalid or expired token")
    return user


def require_admin(current: User = Depends(get_current_user)) -> User:
    """Guarda das rotas administrativas: papel verificado no servidor (403)."""
    if current.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="admin only")
    return current
