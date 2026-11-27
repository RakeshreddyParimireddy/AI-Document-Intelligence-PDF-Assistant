"""App settings, read from the .env file (or real environment variables)."""
from functools import lru_cache
from typing import Literal

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Look for .env in the project root (when run from backend/) or the current folder
    model_config = SettingsConfigDict(env_file=("../.env", ".env"), extra="ignore")

    database_url: str = "postgresql+psycopg://documind:change-me@localhost:5433/documind"
    jwt_secret: str  # required: the app will not start without it
    jwt_expire_minutes: int = 60
    # Which AI answers questions, summarizes and extracts: "claude" or "gemini" (free tier)
    llm_provider: Literal["claude", "gemini"] = "claude"
    llm_api_key: str = ""  # the key for that provider
    llm_model: str = ""  # empty = the provider's default model (see services/llm.py)
    upload_dir: str = "uploads"  # folder where uploaded PDFs are saved
    max_upload_mb: int = 20
    # Longest PDF accepted. On a small server (Render free = 0.1 CPU) a dense page takes
    # about 5 seconds to process, so 30 pages = about 2.5 minutes. Raise it on a bigger plan.
    max_pdf_pages: int = 30
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

    @field_validator("llm_provider", mode="before")
    @classmethod
    def lowercase_provider(cls, value: str) -> str:
        return value.strip().lower() if isinstance(value, str) else value

    @model_validator(mode="after")
    def model_matches_provider(self) -> "Settings":
        """Stop at startup if e.g. LLM_PROVIDER=gemini but LLM_MODEL is a Claude model."""
        model = self.llm_model.strip().lower()
        other = "gemini" if self.llm_provider == "claude" else "claude"
        if model.startswith(other):
            raise ValueError(
                f"LLM_MODEL={self.llm_model} doesn't match LLM_PROVIDER={self.llm_provider}. "
                "Change LLM_MODEL, or leave it empty to use the provider's default model."
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
