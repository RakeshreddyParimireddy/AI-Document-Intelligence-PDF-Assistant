"""Document routes: upload a PDF, list, view, and delete your documents."""
import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.database import SessionLocal, get_db
from app.models import Document, DocumentStatus, User
from app.schemas import DocumentOut
from app.services.pdf_reader import extract_pages

router = APIRouter(prefix="/api/documents", tags=["documents"])

READ_CHUNK_BYTES = 1024 * 1024  # read uploads 1 MB at a time


def pdf_path(document: Document) -> Path:
    """Where a document's PDF is saved on disk: uploads/<user_id>/<document_id>.pdf"""
    return Path(get_settings().upload_dir) / str(document.user_id) / f"{document.id}.pdf"


def get_own_document(document_id: int, user: User, db: Session) -> Document:
    """Find a document that belongs to this user, or return 404.

    We say "not found" (not "forbidden") for other users' documents
    so nobody can learn which document ids exist.
    """
    document = db.scalar(
        select(Document).where(Document.id == document_id, Document.user_id == user.id)
    )
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def process_document(document_id: int) -> None:
    """Runs in the background after upload: read the PDF text page by page.

    It opens its own database session, because the request's session
    is already closed by the time this runs.
    """
    db = SessionLocal()
    try:
        document = db.get(Document, document_id)
        if document is None:  # deleted before processing started
            return
        try:
            pages = extract_pages(str(pdf_path(document)))
            document.pages = len(pages)
            # A scanned PDF (only images) has no text we can use
            has_text = any(page.text for page in pages)
            document.status = DocumentStatus.READY if has_text else DocumentStatus.FAILED
            # Milestone 4 will chunk and embed `pages` here.
        except Exception:
            document.status = DocumentStatus.FAILED
        db.commit()
    finally:
        db.close()


@router.post("/upload", response_model=DocumentOut, status_code=status.HTTP_202_ACCEPTED)
async def upload_document(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    settings = get_settings()
    max_bytes = settings.max_upload_mb * 1024 * 1024

    # 1. Check the name ends with .pdf
    filename = os.path.basename(file.filename or "").strip()
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # 2. Read the file, stopping as soon as it is too big
    data = bytearray()
    while chunk := await file.read(READ_CHUNK_BYTES):
        data.extend(chunk)
        if len(data) > max_bytes:
            raise HTTPException(
                status_code=413, detail=f"File is too large (max {settings.max_upload_mb} MB)"
            )

    # 3. Check the content really is a PDF (every PDF starts with "%PDF-")
    if not data.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="File is not a valid PDF")

    # 4. Save the document row first, so we get an id to name the file with
    document = Document(
        user_id=current_user.id,
        filename=filename[:255],
        size_kb=max(1, round(len(data) / 1024)),
        status=DocumentStatus.PROCESSING,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # 5. Save the PDF to disk
    path = pdf_path(document)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

    # 6. Read the text after the response is sent, so the upload feels fast
    background_tasks.add_task(process_document, document.id)
    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
    ).all()


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return get_own_document(document_id, current_user, db)


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    document = get_own_document(document_id, current_user, db)
    pdf_path(document).unlink(missing_ok=True)
    db.delete(document)
    db.commit()
