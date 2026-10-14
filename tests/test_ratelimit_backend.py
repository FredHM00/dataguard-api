"""Backend do rate limit: testes hermeticos em memoria (Etapa 8).

O caminho Redis e exercitado no CI (mesmo teste de 429, outro backend).
"""

from limits.storage.memory import MemoryStorage

from app.core.rate_limit import limiter


def test_tests_run_on_memory_backend():
    assert isinstance(limiter._storage, MemoryStorage)
