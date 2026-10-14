"""Limitador de requisicoes (slowapi, storage em memoria).

Vale para 1 processo em dev. Com multiplos workers ou maquinas, trocar por
backend Redis; o limite no /login continuaria igual.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])
