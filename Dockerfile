# Imagem enxuta e endurecida (Etapa 13): slim, sem segredos, sem root.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

# Codigo e manifesto juntos: o editable install precisa do pacote presente
# no build (setuptools nao aceita instalar antes de copiar o app/).
COPY pyproject.toml README.md alembic.ini ./
COPY app/ app/
COPY migrations/ migrations/
RUN pip install --no-cache-dir .

# Usuário sem privilégio (uid numérico: compatível com Kubernetes).
RUN useradd --uid 10000 --create-home --shell /bin/false appuser \
    && chown -R 10000:10000 /srv/app
USER 10000:10000

EXPOSE 8000

# Sem ferramentas de debug na imagem: healthcheck em stdlib.
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"

# A API roda atras do Caddy no Compose: confia em X-Forwarded-For/Proto para
# o rate limit enxergar o IP real. Aberto a qualquer origem porque so o
# loopback alcanca a porta direta; em producao, a porta da API nao seria
# publicada (so o proxy falaria com ela).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]
