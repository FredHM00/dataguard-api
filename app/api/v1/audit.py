"""Consulta a trilha de auditoria (somente admin)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.audit.logger import log_action
from app.models.audit_log import AuditAction, AuditLog, AuditResult
from app.models.user import User
from app.schemas.audit import AuditLogList
from app.db.session import get_db

router = APIRouter()


@router.get("", response_model=AuditLogList)
def list_all(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
):
    """Pagina a trilha (a propria leitura e auditada)."""
    size = min(page_size, 100)
    offset = (page - 1) * size
    total = db.scalar(select(func.count()).select_from(AuditLog)) or 0
    entries = db.scalars(
        select(AuditLog).order_by(AuditLog.created_at.desc()).offset(offset).limit(size)
    ).all()
    log_action(
        db,
        actor_id=admin.id,
        action=AuditAction.AUDIT_READ,
        result=AuditResult.SUCCESS,
    )
    db.commit()
    return {"items": entries, "total": total, "page": page, "page_size": size}
