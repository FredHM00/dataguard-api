"""Ponto de entrada da aplicacao FastAPI (DataGuard API)."""

from fastapi import FastAPI

app = FastAPI(title="DataGuard API", version="0.1.0")


@app.get("/health", tags=["infra"])
def health_check() -> dict[str, str]:
    """Verifica se a aplicacao esta no ar.

    Sem autenticacao e sem dados sensiveis: resposta fixa.
    """
    return {"status": "ok"}
