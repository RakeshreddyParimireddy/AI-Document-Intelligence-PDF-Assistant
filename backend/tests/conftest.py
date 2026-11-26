"""Shared test setup.

- Uses a SEPARATE database (<your db name>_test), so tests never touch real data.
- Uses a temporary folder for uploads.
- Never calls the real LLM: there is no API key, and LLM tests replace the client with a fake.

Everything above the `from app...` imports must run first, because the app reads
its settings (like DATABASE_URL) when it is imported.
"""
import os
import tempfile

os.environ.setdefault("JWT_SECRET", "test-secret")
os.environ["LLM_API_KEY"] = ""  # tests must never use a real key
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="documind-test-uploads-")

from sqlalchemy import create_engine, text  # noqa: E402
from sqlalchemy.engine import make_url  # noqa: E402

from app.config import get_settings  # noqa: E402

# Point the app at the test database: same server, database name + "_test"
_real_url = make_url(get_settings().database_url)
TEST_DB_NAME = f"{_real_url.database}_test"
_test_url = _real_url.set(database=TEST_DB_NAME)
os.environ["DATABASE_URL"] = _test_url.render_as_string(hide_password=False)
get_settings.cache_clear()


def _create_test_database():
    """Create the test database (once) and turn on pgvector in it."""
    admin = create_engine(_real_url.set(database="postgres"), isolation_level="AUTOCOMMIT")
    with admin.connect() as conn:
        exists = conn.scalar(
            text("SELECT 1 FROM pg_database WHERE datname = :name"), {"name": TEST_DB_NAME}
        )
        if not exists:
            conn.execute(text(f'CREATE DATABASE "{TEST_DB_NAME}"'))
    admin.dispose()
    test_engine = create_engine(_test_url, isolation_level="AUTOCOMMIT")
    with test_engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    test_engine.dispose()


_create_test_database()

import shutil  # noqa: E402
from pathlib import Path  # noqa: E402

import pymupdf  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

assert engine.url.database == TEST_DB_NAME, "Tests must run against the test database"


# ---------- Sample PDF text (generated, so the tests need no files) ----------
INVOICE_PAGES = [
    "ACME Supplies Ltd. - INVOICE. Invoice number: INV-2026-0042. Invoice date: 12 March 2026. "
    "Bill to: Northwind Traders. 50 office chairs and 20 standing desks. "
    "Total amount due: $14,850.00",
    "Payment Terms. Payment is due within 30 days of the invoice date. "
    "A late fee of 2% per month applies to overdue balances.",
    "Contacts. Sales contact: Maria Lopez. Accounts contact: James Chen.",
]
HANDBOOK_PAGES = [
    "Employee Handbook. Working hours are 9:00 AM to 5:30 PM. "
    "Remote work: employees may work from home up to three days per week.",
    "Annual Leave and Holidays. Full-time employees receive 25 days of paid annual leave "
    "per year, plus public holidays. Sick leave: 10 days of paid sick leave per year.",
    "Expenses and Reimbursement. Submit receipts within 30 days. "
    "Meals are reimbursed up to $60 per person per day.",
    "IT and Security. Never share your password. Turn on two-factor authentication. "
    "Report lost or stolen laptops to the security team within one hour.",
]


def make_pdf(pages: list[str]) -> bytes:
    """Build a PDF in memory with one page per text."""
    doc = pymupdf.open()
    for page_text in pages:
        page = doc.new_page()
        if page_text:
            page.insert_textbox(pymupdf.Rect(50, 50, 550, 800), page_text, fontsize=11)
    data = doc.tobytes()
    doc.close()
    return data


# ---------- Fixtures ----------
@pytest.fixture(scope="session")
def client():
    """A test client for the API. `with` runs the app's startup (creates tables, loads model)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def clean_state(client):
    """Before every test: empty all tables and the uploads folder."""
    table_names = ", ".join(table.name for table in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {table_names} RESTART IDENTITY CASCADE"))
    upload_dir = Path(get_settings().upload_dir)
    shutil.rmtree(upload_dir, ignore_errors=True)
    upload_dir.mkdir(parents=True, exist_ok=True)
    yield


@pytest.fixture
def make_user(client):
    """Register a user and return their auth headers: headers = make_user("a@x.com")."""

    def _make_user(email: str = "alice@example.com", password: str = "secret123") -> dict:
        response = client.post("/api/auth/register", json={"email": email, "password": password})
        assert response.status_code == 201, response.text
        response = client.post("/api/auth/login", data={"username": email, "password": password})
        assert response.status_code == 200, response.text
        return {"Authorization": f"Bearer {response.json()['access_token']}"}

    return _make_user


@pytest.fixture
def upload(client):
    """Upload a PDF and return the API response: upload(headers, pages, "name.pdf")."""

    def _upload(headers: dict, pages: list[str], filename: str = "test.pdf"):
        files = {"file": (filename, make_pdf(pages), "application/pdf")}
        return client.post("/api/documents/upload", headers=headers, files=files)

    return _upload
