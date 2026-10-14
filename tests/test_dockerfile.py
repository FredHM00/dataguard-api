"""Endurecimento do container como teste: Dockerfile e .dockerignore (Etapa 13).

Politica executavel: se alguem voltar ao root ou vazar segredo para a imagem,
a suite quebra aqui, nao em producao. Checagens precisas (substring puro
daria falso positivo nos proprios comentarios).
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(name: str) -> str:
    return (ROOT / name).read_text(encoding="utf-8")


def test_dockerfile_runs_as_non_root():
    body = _read("Dockerfile")
    assert "USER 10000:10000" in body
    assert "USER root" not in body
    assert "USER 0" not in body


def test_dockerfile_has_no_secrets_or_debug_tools():
    body = _read("Dockerfile")
    assert "COPY .env" not in body
    assert "ADD .env" not in body
    assert not re.search(r"^\s*ENV\s+\w*(PASSWORD|SECRET|KEY)\w*\s*=", body, re.M)
    assert "curl" not in body
    assert "wget" not in body


def test_dockerignore_blocks_secrets_and_tooling():
    body = _read(".dockerignore")
    for blocked in (".env", ".venv/", ".git/", "tests/", "__pycache__/"):
        assert blocked in body, f"{blocked} deveria estar no .dockerignore"


def test_docker_healthcheck_uses_stdlib():
    body = _read("Dockerfile")
    assert "HEALTHCHECK" in body
    assert "/health" in body
