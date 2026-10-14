"""Schemas dos registros (Pydantic v2).

- Create sem "status": todo registro nasce open; sem owner_id (vem do JWT).
- Update parcial com Literal: status invalido morre com 422 automatico.
- Read expoe "notes" em texto puro SOMENTE ao dono autorizado.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

RecordStatusIn = Literal["open", "in_progress", "closed"]


class RecordCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=50)
    notes: str = Field(min_length=1, max_length=10000)


class RecordUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=50)
    notes: str | None = Field(default=None, min_length=1, max_length=10000)
    status: RecordStatusIn | None = None


class RecordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    category: str
    notes: str
    status: str
    created_at: datetime
    updated_at: datetime


class RecordList(BaseModel):
    items: list[RecordRead]
    total: int
    page: int
    page_size: int


class RecordCursorPage(BaseModel):
    items: list[RecordRead]
    next_cursor: str | None
