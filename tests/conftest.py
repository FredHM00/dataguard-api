"""Isolamento dos testes: banco dataguard_test + rollback por teste.

Cada teste ve um banco vazio e nada que ele faca sobrevive ao teste.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.session import get_db
from app.main import app


def _test_database_url() -> str:
    base = settings.database_url
    return base.rsplit("/", 1)[0] + "/dataguard_test"


test_engine = create_engine(_test_database_url())
TestingSession = sessionmaker(bind=test_engine, autoflush=False, expire_on_commit=False)


@pytest.fixture(scope="session", autouse=True)
def _schema():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield


@pytest.fixture()
def client():
    from app.core.rate_limit import limiter as _limiter  # noqa: PLC0415

    _limiter._storage.reset()  # isolamento: zera o rate limit entre testes
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSession(bind=connection)

    def _override():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = _override
    with TestClient(app) as test_client:
        test_client.db = session  # acesso a mesma transacao do teste
        yield test_client
    app.dependency_overrides.clear()
    session.close()
    transaction.rollback()
    connection.close()
