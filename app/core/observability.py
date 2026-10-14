"""Observabilidade de bancada: request-id, access log e metricas minimas.

- X-Request-ID: aceita o do cliente ou gera; sempre devolvido (rastreio).
- Access log: method/path sanitizado/status/duracao. NUNCA query string
  (pode carregar segredo em URL) nem corpo.
- Metricas em memoria (mesma ressalva do limiter em memoria: por processo).
  Suficiente para laboratorio; Prometheus real exigiria client oficial.
"""

import re
import threading
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging_config import get_logger

_UUID_RE = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

access_log = get_logger("access")

_lock = threading.Lock()
_requests_total: dict[tuple[str, str, int], int] = {}
_errors_total = 0


def sanitize_path(path: str) -> str:
    """Troca UUIDs por {id}: cardinalidade limitada nas metricas e logs."""
    return _UUID_RE.sub("{id}", path)


def record_request(route: str, method: str, status_code: int) -> None:
    """Incrementa contadores (thread-safe; por processo)."""
    global _errors_total
    with _lock:
        key = (route, method, status_code)
        _requests_total[key] = _requests_total.get(key, 0) + 1
        if status_code >= 500:
            _errors_total += 1


def render_metrics() -> str:
    """Exposicao texto no formato Prometheus (texto simples, sem client)."""
    lines = [
        "# HELP dataguard_http_requests_total Total de requisicoes HTTP.",
        "# TYPE dataguard_http_requests_total counter",
    ]
    with _lock:
        for (route, method, status_code), total in sorted(_requests_total.items()):
            lines.append(
                f'dataguard_http_requests_total{{route="{route}",'
                f'method="{method}",status="{status_code}"}} {total}'
            )
        lines += [
            "# HELP dataguard_http_errors_total Total de respostas 5xx.",
            "# TYPE dataguard_http_errors_total counter",
            f"dataguard_http_errors_total {_errors_total}",
        ]
    return "\n".join(lines) + "\n"


class ObservabilityMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        request_id = dict(scope.get("headers", [])).get(b"x-request-id", b"").decode()
        if not request_id:
            request_id = uuid.uuid4().hex
        method = scope.get("method", "?")
        route = sanitize_path(scope.get("path", "?"))
        started = time.perf_counter()
        status_code = 500

        async def send_with_context(message: Message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                headers = MutableHeaders(raw=message.setdefault("headers", []))
                headers["X-Request-ID"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_context)
        finally:
            duration_ms = round((time.perf_counter() - started) * 1000, 2)
            record_request(route, method, status_code)
            access_log.info(
                "request",
                extra={
                    "request_id": request_id,
                    "method": method,
                    "path": route,
                    "status": status_code,
                    "duration_ms": duration_ms,
                },
            )
