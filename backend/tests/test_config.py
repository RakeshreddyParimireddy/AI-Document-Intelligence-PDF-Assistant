"""Settings tests."""
import pytest
from pydantic import ValidationError

from app.config import Settings


def database_url(url: str) -> str:
    return Settings(jwt_secret="x", database_url=url).database_url


def test_hosted_database_urls_get_the_psycopg_driver():
    # The kind of URL Neon / other hosts give you
    assert database_url("postgresql://u:p@host/db?sslmode=require") == (
        "postgresql+psycopg://u:p@host/db?sslmode=require"
    )
    assert database_url("postgres://u:p@host/db") == "postgresql+psycopg://u:p@host/db"


def test_urls_that_already_name_the_driver_are_unchanged():
    url = "postgresql+psycopg://u:p@localhost:5433/db"
    assert database_url(url) == url


def test_provider_and_model_must_match():
    with pytest.raises(ValidationError, match="doesn't match"):
        Settings(jwt_secret="x", llm_provider="gemini", llm_model="claude-opus-5-5")
    with pytest.raises(ValidationError, match="doesn't match"):
        Settings(jwt_secret="x", llm_provider="claude", llm_model="gemini-3.5-flash-lite")
    # Empty model = the provider's default; provider names are case-insensitive
    assert Settings(jwt_secret="x", llm_provider="Gemini", llm_model="").llm_provider == "gemini"
