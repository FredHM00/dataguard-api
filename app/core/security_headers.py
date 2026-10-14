"""Cabecalhos de seguranca minimalistas para API JSON (Etapa 11).

- Cache-Control: no-store: respostas autenticadas nao devem parar em cache
  de intermediario (o ZAP acusou 404s "cacheable"; o principio vale para tudo).
- X-Content-Type-Options: nosniff: sem MIME-sniffing nas respostas.
Sem o kit "helmet" completo de proposito: sem conteudo browser (sem HTML
proprio alem do /docs em dev), frame/CSP nao se aplicam.
"""

from starlette.datastructures import MutableHeaders
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class SecurityHeadersMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = MutableHeaders(raw=message.setdefault("headers", []))
                headers["Cache-Control"] = "no-store"
                headers["X-Content-Type-Options"] = "nosniff"
            await send(message)

        await self.app(scope, receive, send_with_headers)
