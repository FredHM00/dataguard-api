"""Configuracoes lidas de variaveis de ambiente (arquivo .env local).

Nenhum segredo mora no codigo: tudo sensivel chega por ambiente.
JWT_SECRET_KEY e FERNET_KEY nao tem default: sem eles a app nem importa.
"""

from datetime import timedelta

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Banco (Etapa 2) + JWT (Etapa 3) + Fernet (Etapa 4) + refresh (Etapa 7)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    POSTGRES_USER: str = "dataguard"
    # Sem default de proposito (endurecido via Bandit na Etapa 5): mesmo sendo
    # so o banco local, segredo nao mora no codigo. O .env fornece o valor.
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "dataguard"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None

    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 30

    FERNET_KEY: str

    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Onde o slowapi guarda os contadores: memoria local (1 processo, dev/teste)
    # ou redis://... (multiplos workers/maquinas). Testes forcam memoria.
    RATELIMIT_STORAGE_URI: str = "memory://"

    @property
    def database_url(self) -> str:
        """Monta a URL do SQLAlchemy; DATABASE_URL tem precedencia se definida."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def refresh_expires(self) -> timedelta:
        """Vida util do refresh token (longa; o access continua curto)."""
        return timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)


settings = Settings()
