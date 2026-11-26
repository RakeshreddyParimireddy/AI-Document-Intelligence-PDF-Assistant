"""App settings, read from the .env file (or real environment variables)."""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Look for .env in the project root (when run from backend/) or the current folder
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str = "postgresql+psycopg://documind:change-me@localhost:5433/documind"
    jwt_secret: str = "change-me"
    llm_api_key: str = ""


@lru_cache
def get_settings() -> Settings:
    return Settings()
