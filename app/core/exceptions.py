"""Excecoes de dominio: services levantam, rotas traduzem para HTTP."""


class DuplicateEmail(Exception):
    """Cadastro com e-mail ja existente (vira 409)."""


class InvalidCredentials(Exception):
    """Login invalido sem dizer o motivo (vira 401 generico)."""


class InvalidToken(Exception):
    """JWT ausente, adulterado, expirado ou malformado (vira 401)."""
