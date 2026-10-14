"""Politica TLS como teste: Caddyfile e Compose (Etapa 14)."""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_caddy_terminates_tls_with_internal_ca():
    body = _read("docker/caddy/Caddyfile")
    assert "tls internal" in body
    assert "reverse_proxy api:8000" in body
    assert "admin off" in body


def test_caddy_sends_hsts():
    body = _read("docker/caddy/Caddyfile")
    assert "Strict-Transport-Security" in body
    assert "max-age=" in body


def test_no_plaintext_http_listener():
    body = _read("docker/caddy/Caddyfile")
    assert re.search(r"(?<!s)http://", body) is None  # http:// puro (https:// ok)
    assert re.search(r":80\b", body) is None  # porta 80 (8000 ok)


def test_compose_publishes_only_loopback_https():
    body = _read("compose.yaml")
    assert "127.0.0.1:443:443" in body
    assert "caddy:2-alpine" in body


def test_api_trusts_proxy_headers():
    body = _read("Dockerfile")
    assert "--proxy-headers" in body
