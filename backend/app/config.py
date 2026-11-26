"""App settings, read from the .env file (or real environment variables)."""
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Look for .env in the project root (when run from backend/) or the current folder
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str = "postgresql+psycopg://documind:change-me@localhost:5433/documind"
    jwt_secret: str  # required: the app will not start without it
    jwt_expire_minutes: int = 60
    llm_api_key: str = ""
    llm_model: str = "claude-opus-5-5"
    upload_dir: str = "uploads"  # folder where uploaded PDFs are saved
    max_upload_mb: int = 20
    # Website addresses allowed to call this API from a browser (comma-separated)
    cors_origins: str = "http://localhost:3000"

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, url: str) -> str:
        """Hosts like Neon give "postgresql://..." or "postgres://..." URLs.
        SQLAlchemy needs "postgresql+psycopg://..." to use the psycopg driver."""
        for prefix in ("postgres://", "postgresql://"):
            if url.startswith(prefix):
                return "postgresql+psycopg://" + url[len(prefix):]
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
