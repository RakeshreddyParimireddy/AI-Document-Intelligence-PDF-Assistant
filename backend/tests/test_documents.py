"""Upload tests: validation, processing (read -> chunk -> embed), ownership, delete."""
from pathlib import Path

from sqlalchemy import func, select

from app.config import get_settings
from app.database import SessionLocal
from app.models import Chunk
from tests.conftest import INVOICE_PAGES, make_pdf


def chunk_count(document_id: int) -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(Chunk).where(Chunk.document_id == document_id))


def test_upload_processes_the_pdf(client, make_user, upload):
    headers = make_user()
    response = upload(headers, INVOICE_PAGES, "invoice.pdf")
    assert response.status_code == 202
    assert response.json()["status"] == "processing"
    doc_id = response.json()["id"]

    # The test client runs the background processing before returning
    doc = client.get(f"/api/documents/{doc_id}", headers=headers).json()
    assert doc["status"] == "ready"
    assert doc["pages"] == 3
    assert doc["filename"] == "invoice.pdf"
    assert chunk_count(doc_id) == 3  # one short chunk per page

    with SessionLocal() as db:
        pages = sorted(db.scalars(select(Chunk.page_number).where(Chunk.document_id == doc_id)))
        dims = db.scalar(select(func.vector_dims(Chunk.embedding)).limit(1))
    assert pages == [1, 2, 3]
    assert dims == 384


def test_only_pdf_files_are_accepted(client, make_user):
    headers = make_user()
    files = {"file": ("notes.txt", b"hello", "text/plain")}
    response = client.post("/api/documents/upload", headers=headers, files=files)
    assert response.status_code == 400


def test_fake_pdf_is_rejected(client, make_user):
    headers = make_user()
    files = {"file": ("fake.pdf", b"this is not a pdf", "application/pdf")}
    response = client.post("/api/documents/upload", headers=headers, files=files)
    assert response.status_code == 400


def test_too_large_file_is_rejected(client, make_user, monkeypatch):
    monkeypatch.setattr(get_settings(), "max_upload_mb", 1)
    headers = make_user()
    big = b"%PDF-" + b"0" * (2 * 1024 * 1024)  # 2 MB
    files = {"file": ("big.pdf", big, "application/pdf")}
    response = client.post("/api/documents/upload", headers=headers, files=files)
    assert response.status_code == 413


def test_pdf_without_text_is_marked_failed(client, make_user, upload):
    headers = make_user()
    doc_id = upload(headers, ["", ""], "scanned.pdf").json()["id"]
    doc = client.get(f"/api/documents/{doc_id}", headers=headers).json()
    assert doc["status"] == "failed"
    assert chunk_count(doc_id) == 0


def test_upload_requires_login(client):
    files = {"file": ("a.pdf", make_pdf(["x"]), "application/pdf")}
    assert client.post("/api/documents/upload", files=files).status_code == 401


def test_users_only_see_their_own_documents(client, make_user, upload):
    alice, bob = make_user("alice@example.com"), make_user("bob@example.com")
    doc_id = upload(alice, INVOICE_PAGES).json()["id"]

    assert len(client.get("/api/documents", headers=alice).json()) == 1
    assert client.get("/api/documents", headers=bob).json() == []
    assert client.get(f"/api/documents/{doc_id}", headers=bob).status_code == 404
    assert client.delete(f"/api/documents/{doc_id}", headers=bob).status_code == 404
    # Bob's failed delete didn't remove anything
    assert client.get(f"/api/documents/{doc_id}", headers=alice).status_code == 200


def test_delete_removes_document_file_and_chunks(client, make_user, upload):
    headers = make_user()
    doc_id = upload(headers, INVOICE_PAGES).json()["id"]
    pdf_files = list(Path(get_settings().upload_dir).rglob("*.pdf"))
    assert len(pdf_files) == 1

    assert client.delete(f"/api/documents/{doc_id}", headers=headers).status_code == 204
    assert client.get(f"/api/documents/{doc_id}", headers=headers).status_code == 404
    assert chunk_count(doc_id) == 0
    assert not pdf_files[0].exists()
