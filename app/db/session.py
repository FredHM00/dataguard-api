"""Engine SQLAlchemy 2.x + sessao por requisicao.

- pool_pre_ping=True: descarta conexoes mortas antes de usar (evita erros
  transientes quando o banco reinicia).
- expire_on_commit=False: objetos continuam legiveis apos o commit, sem
  SELECTs extras silenciosos.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """Dependencia FastAPI: abre, entrega e sempre fecha a sessao."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
