"""Ponto de entrada da aplicacao FastAPI (DataGuard API)."""

from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.api.v1.router import api_router
from app.core.rate_limit import limiter

app = FastAPI(title="DataGuard API", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.include_router(api_router)


@app.get("/health", tags=["infra"])
def health_check() -> dict[str, str]:
    """Verifica se a aplicacao esta no ar.

    Sem autenticacao e sem dados sensiveis: resposta fixa.
    """
    return {"status": "ok"}
