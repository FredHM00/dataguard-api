"""Base declarativa dos modelos + convencao de nomes para constraints.

Nomes deterministicos (uq_users_email em vez de hash aleatorio) deixam as
migracoes futuras legiveis e reversiveis.
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Todos os modelos herdam daqui; o Alembic le este metadata."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
