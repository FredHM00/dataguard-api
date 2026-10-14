"""Logging JSON estruturado (stdlib, sem dependencia nova).

Uma linha por requisicao (ver ObservabilityMiddleware), nunca com corpo,
query string ou header sensivel. Logs de negocio sensiveis vao para a tabela
audit_logs, nao para stdout.
"""

import json
import logging
from datetime import datetime, timezone

_RESERVED = frozenset(
    {
        "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
        "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
        "created", "msecs", "relativeCreated", "thread", "threadName",
        "processName", "process", "message", "asctime", "taskName",
    }
)


class JsonFormatter(logging.Formatter):
    """Serializa o LogRecord como um objeto JSON por linha."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        return json.dumps(payload, default=str)


def configure_logging(level: str = "INFO") -> None:
    """Configura o logger 'dataguard' (idempotente entre imports/testes)."""
    logger = logging.getLogger("dataguard")
    if logger.handlers:
        return
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Atalho: logging.getLogger('dataguard.<name>')."""
    return logging.getLogger(f"dataguard.{name}")
