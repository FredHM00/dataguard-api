"""Configuracoes lidas de variaveis de ambiente (arquivo .env local).

Nenhum segredo mora no codigo: tudo sensivel chega por ambiente.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Ajustes de conexao com o banco (Etapa 2; JWT/Fernet entram na Etapa 3/4)."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    POSTGRES_USER: str = "dataguard"
    POSTGRES_PASSWORD: str = "dataguard-dev-only"
    POSTGRES_DB: str = "dataguard"
    POSTGRES_HOST: str = "127.0.0.1"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None

    @property
    def database_url(self) -> str:
        """Monta a URL do SQLAlchemy; DATABASE_URL tem precedencia se definida."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )


settings = Settings()
