"""Refresh tokens opacos: texto puro so na resposta, hash no banco.

O token tem 256 bits de entropia (secrets), entao SHA-256 como hash de
armazenamento e suficiente (Argon2 seria custo sem beneficio aqui).
"""

import hashlib
import secrets


def generate_refresh_token() -> str:
    """Gera o texto puro (transmitido uma unica vez, nunca persistido)."""
    return secrets.token_urlsafe(48)


def hash_refresh_token(token: str) -> str:
    """SHA-256 hex para busca/unicidade sem expor a sessao em repouso."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
