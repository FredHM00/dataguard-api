"""Schema do token de acesso (resposta do /login)."""

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
