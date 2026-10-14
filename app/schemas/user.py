"""Schemas de entrada/saida para usuarios e autenticacao (Pydantic v2).

extra="forbid" nos inputs: campo desconhecido (ex.: "role") e rejeitado com
422 em vez de silenciosamente ignorado.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Cadastro publico: email + senha. Sem campo de papel, por design."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Credenciais de login (o endpoint real usa form OAuth2; este schema
    documenta o formato e serve aos testes)."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str


class UserRead(BaseModel):
    """Perfil publico: nunca inclui hash, nunca inclui nada sensivel."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime
