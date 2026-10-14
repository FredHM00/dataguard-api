"""Criptografia das observacoes sensiveis (Fernet = AES128-CBC + HMAC).

KeyRing: cifra com a primeira chave, decifra tentando todas em ordem.
Permite rotacao sem downtime (etapas no README). Sem nenhuma chave valida,
o import quebra com erro claro (falha fechada, sem fallback).
"""

from cryptography.fernet import Fernet, InvalidToken as FernetInvalidToken

from app.core.config import settings
from app.core.exceptions import DecryptionError


def parse_keys(raw: str | None, legacy: str | None) -> list[str]:
    """Normaliza a configuracao: lista separada por virgula ou chave unica legada."""
    if raw:
        keys = [part.strip() for part in raw.split(",") if part.strip()]
        if keys:
            return keys
    if legacy and legacy.strip():
        return [legacy.strip()]
    return []


class KeyRing:
    """Conjunto ordenado de chaves: [primaria, anteriores...]."""

    def __init__(self, keys: list[str]) -> None:
        if not keys:
            raise ValueError("keyring vazio: defina FERNET_KEYS (ou FERNET_KEY legado)")
        self._fernets = [Fernet(key.encode("utf-8")) for key in keys]

    def encrypt(self, plain_text: str) -> str:
        """Cifra sempre com a primaria; devolve token ASCII para coluna Text."""
        return self._fernets[0].encrypt(plain_text.encode("utf-8")).decode("utf-8")

    def decrypt(self, token: str) -> str:
        """Tenta cada chave em ordem; se nenhuma abrir, DecryptionError."""
        for fernet in self._fernets:
            try:
                return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
            except (FernetInvalidToken, ValueError):
                continue
        raise DecryptionError()


def _load_keys() -> list[str]:
    keys = parse_keys(settings.FERNET_KEYS, settings.FERNET_KEY)
    if not keys:
        raise RuntimeError(
            "nenhuma chave Fernet configurada: defina FERNET_KEYS "
            "(ou FERNET_KEY legado) no .env"
        )
    return keys


keyring = KeyRing(_load_keys())


def encrypt_note(plain_text: str) -> str:
    """Cifra com o anel padrao (primaria atual)."""
    return keyring.encrypt(plain_text)


def decrypt_note(token: str) -> str:
    """Decifra com o anel padrao (qualquer chave valida)."""
    return keyring.decrypt(token)
