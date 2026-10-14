"""Endpoints de autenticacao: cadastro, login, refresh e logout."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateEmail, InvalidCredentials, InvalidToken
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import LogoutRequest, RefreshRequest, Token
from app.schemas.user import UserCreate, UserRead
from app.services import refresh_service, user_service

router = APIRouter()


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    """Cadastra usuario comum. O campo "role" nem existe no schema (422 se enviado)."""
    try:
        return user_service.register_user(db, email=payload.email, password=payload.password)
    except DuplicateEmail:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="email already registered"
        ) from None


@router.post("/login", response_model=Token)
@limiter.limit("10/minute")
def login(
    request: Request,
    form: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
) -> dict[str, str]:
    """Autentica e emite o par access (30min) + refresh (7 dias, uso unico)."""
    try:
        user = user_service.authenticate(db, email=form.username, password=form.password)
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return refresh_service.issue_pair(db, user)


@router.post("/refresh", response_model=Token)
@limiter.limit("10/minute")
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)) -> dict[str, str]:
    """Troca um refresh valido por um par novo (rotacao; reuso = 401 + revoga tudo)."""
    try:
        return refresh_service.rotate(db, payload.refresh_token)
    except InvalidToken:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid or expired refresh token",
        ) from None


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(payload: LogoutRequest, db: Session = Depends(get_db)) -> None:
    """Revoga o refresh (idempotente: desconhecido tambem devolve 204)."""
    refresh_service.revoke(db, payload.refresh_token)
    return None
