"""CRUD de registros: posse verificada no servidor, pagina com teto."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.exceptions import DecryptionError, NotFound
from app.db.session import get_db
from app.models.user import User
from app.schemas.record import RecordCreate, RecordList, RecordRead, RecordUpdate
from app.services import record_service

router = APIRouter()


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="record not found")


@router.post("", response_model=RecordRead, status_code=status.HTTP_201_CREATED)
def create(payload: RecordCreate, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Cria um registro do usuario autenticado (status sempre nasce open)."""
    return record_service.create_record(
        db, owner=current, title=payload.title, category=payload.category, notes=payload.notes
    )


@router.get("", response_model=RecordList)
def list_all(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Lista paginada dos autorizados; page_size tem teto anti-abuso (100)."""
    items, total = record_service.list_records(db, requester=current, page=page, page_size=page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/{record_id}", response_model=RecordRead)
def get_one(record_id: UUID, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Consulta individual; alheio ou inexistente responde igual: 404."""
    try:
        return record_service.get_record(db, record_id=record_id, requester=current)
    except NotFound:
        raise _not_found() from None
    except DecryptionError:
        raise HTTPException(status_code=500, detail="internal error") from None


@router.patch("/{record_id}", response_model=RecordRead)
def update(
    record_id: UUID,
    payload: RecordUpdate,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """Atualizacao parcial com guard de posse + auditoria."""
    try:
        return record_service.update_record(
            db,
            record_id=record_id,
            requester=current,
            title=payload.title,
            category=payload.category,
            notes=payload.notes,
            status=payload.status,
        )
    except NotFound:
        raise _not_found() from None
    except DecryptionError:
        raise HTTPException(status_code=500, detail="internal error") from None


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(record_id: UUID, db: Session = Depends(get_db), current: User = Depends(get_current_user)):
    """Remocao com guard de posse + auditoria; sem corpo na resposta."""
    try:
        record_service.delete_record(db, record_id=record_id, requester=current)
    except NotFound:
        raise _not_found() from None
    return None
