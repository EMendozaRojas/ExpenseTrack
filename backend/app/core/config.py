from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    backend_cors_origins: str = "http://localhost:5173"

    attachments_dir: str = "/app/storage/attachments"

    google_client_id: str = ""
    google_client_secret: str = ""
    google_redirect_uri: str = "http://localhost:8000/api/v1/auth/oauth/google/callback"
    frontend_base_url: str = "http://localhost:5173"
    refresh_token_expire_days: int = 30

    # SMTP vacío (default) = envío de email deshabilitado (p. ej. en tests).
    # En local apunta a Mailhog (docker-compose), que nunca entrega a internet.
    smtp_host: str = ""
    smtp_port: int = 1025
    smtp_from: str = "notificaciones@expensetrack.local"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.backend_cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
