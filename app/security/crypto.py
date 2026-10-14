"""Criptografia das observacoes sensiveis (Fernet = AES128-CBC + HMAC).

O objeto e criado no import: chave ausente ou invalida quebra o boot com erro
claro, em vez de operar sem criptografia ou com fallback fixo.
"""

from cryptography.fernet import Fernet, InvalidToken as FernetInvalidToken

from app.core.config import settings
from app.core.exceptions import DecryptionError

fernet = Fernet(settings.FERNET_KEY.encode("utf-8"))


def encrypt_note(plain_text: str) -> str:
    """Cifra o texto puro; devolve token ASCII seguro para coluna Text."""
    return fernet.encrypt(plain_text.encode("utf-8")).decode("utf-8")


def decrypt_note(token: str) -> str:
    """Decifra apos autorizacao validada; falha vira DecryptionError (500)."""
    try:
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except (FernetInvalidToken, ValueError):
        raise DecryptionError() from None
