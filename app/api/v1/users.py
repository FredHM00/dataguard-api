"""Endpoints do proprio usuario autenticado."""

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.user import UserRead

router = APIRouter()


@router.get("/me", response_model=UserRead)
def read_me(current: User = Depends(get_current_user)) -> User:
    """Devolve o perfil de quem apresenta um JWT valido."""
    return current
