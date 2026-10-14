"""Import central dos modelos: o Alembic precisa deles carregados."""

from app.models.audit_log import AuditLog  # noqa: F401
from app.models.record import Record  # noqa: F401
from app.models.user import User  # noqa: F401
