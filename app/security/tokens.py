"""Emissao e validacao de JWT (PyJWT, HS256).

JWT assinado NAO e criptografado: o payload e legivel por qualquer um.
Por isso as claims carregam so o essencial (sub + expiracao).
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt

from app.core.config import settings
from app.core.exceptions import InvalidToken

#: Rotulo OAuth2 do tipo de token (RFC 6750). Constante central para o Bandit
#: nao confundir com senha hardcoded em cada dicionario de resposta.
TOKEN_TYPE = "bearer"  # nosec B105: rotulo OAuth2 (RFC 6750), nao senha


def create_access_token(user_id: UUID) -> str:
    """Assina um token com sub=id do usuario e expiracao configurada."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "iat": now,
        "exp": now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> UUID:
    """Valida assinatura + expiracao e devolve o id do usuario.

    Qualquer problema (adulterado, expirado, sub invalido) vira InvalidToken:
    o chamador responde 401 generico sem detalhar o motivo.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return UUID(str(payload.get("sub")))
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError, AttributeError):
        raise InvalidToken() from None
