"""Settings tests."""
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
