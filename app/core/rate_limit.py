"""Limitador de requisicoes (slowapi).

Storage configuravel: memoria por padrao (1 processo, dev/teste) ou Redis
(multiplos workers/maquinas) via RATELIMIT_STORAGE_URI. Contadores sao
efemeros: perder o Redis apenas afrouxa o limite por uma janela.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

from app.core.config import settings

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute"],
    storage_uri=settings.RATELIMIT_STORAGE_URI,
)
