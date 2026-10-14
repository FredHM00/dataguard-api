"""Endpoints de autenticacao: cadastro e login."""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.exceptions import DuplicateEmail, InvalidCredentials
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.user import User
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead
from app.security.tokens import create_access_token
from app.services import user_service

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
    """Autentica e emite JWT. Form OAuth2: o campo "username" carrega o e-mail."""
    try:
        user = user_service.authenticate(db, email=form.username, password=form.password)
    except InvalidCredentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}
