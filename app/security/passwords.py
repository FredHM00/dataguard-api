"""Hash e verificacao de senhas com Argon2 (vencedor do PHC).

So trafegam hashes PHC (ex.: $argon2id$v=19$...); texto puro nunca e logado,
nunca e persistido, nunca entra no JWT.
"""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHash, VerificationError, VerifyMismatchError

_ph = PasswordHasher()


def hash_password(plain_password: str) -> str:
    """Gera o hash PHC com salt aleatorio (cada chamada, um hash diferente)."""
    return _ph.hash(plain_password)


def verify_password(stored_hash: str, candidate: str) -> bool:
    """Compara em tempo aproximadamente constante; False em qualquer falha."""
    try:
        return _ph.verify(stored_hash, candidate)
    except (VerifyMismatchError, VerificationError, InvalidHash):
        return False


# Hash valido usado quando o e-mail nem existe: mantem o tempo de resposta
# parecido e nao revela quais e-mails estao cadastrados.
DUMMY_HASH = hash_password("dataguard-dummy-password")
