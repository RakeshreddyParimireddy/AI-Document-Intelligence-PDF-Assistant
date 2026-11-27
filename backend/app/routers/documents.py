"""Document routes: upload a PDF, list, view, and delete your documents."""
import logging
import threading
import time
import os
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import get_settings
from app.database import SessionLocal, get_db
from app.models import DocumentPage, Chunk, Document, DocumentStatus, User
from app.schemas import DocumentOut, SearchRequest, SearchResult
from app.services.chunker import chunk_pages
from app.services.embeddings import embed_texts
from app.services.pdf_reader import count_pages, extract_pages
from app.services.retriever import search_chunks

logger = logging.getLogger(__name__)
EMBED_PROGRESS_EVERY = 64  # log embedding progress after every 64 chunks

# Process one document at a time. On a small server two at once would each take twice
# as long (and use twice the memory); one after the other, the first is ready sooner,
# and users' questions only have to share the CPU with one job.
_processing_lock = threading.Lock()
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
    """Runs in the background after upload: read -> chunk -> embed -> store.

    It opens its own database session, because the request's session
    is already closed by the time this runs. Afterwards the PDF file is deleted:
    everything we need (page text, chunks, vectors) is in the database.
    """
    with _processing_lock:
        _process_document(document_id)


def _process_document(document_id: int) -> None:
    db = SessionLocal()
    path = None
    try:
        document = db.get(Document, document_id)
        if document is None:  # deleted before processing started
            return
        path = pdf_path(document)
        started = time.monotonic()
        logger.info("Document %s: processing started", document_id)
        try:
            # 1. Read the text of each page, and keep it (for Summary and Extract)
            pages = extract_pages(str(path))
            document.pages = len(pages)
            db.add_all(
                DocumentPage(document_id=document.id, page_number=page.page_number, text=page.text)
                for page in pages
                if page.text
            )

            # 2. Split into chunks (each remembers its page number)
            chunks = chunk_pages(pages)
            logger.info(
                "Document %s: read %d pages -> %d chunks", document_id, len(pages), len(chunks)
            )

            # A scanned PDF (only images) has no text we can use
            if not chunks:
                document.status = DocumentStatus.FAILED
            else:
                # 3. Turn every chunk into a vector (in parts, so progress shows in the logs)
                vectors = []
                for start in range(0, len(chunks), EMBED_PROGRESS_EVERY):
                    part = chunks[start : start + EMBED_PROGRESS_EVERY]
                    vectors.extend(embed_texts([chunk.content for chunk in part]))
                    logger.info(
                        "Document %s: embedded %d/%d chunks", document_id, len(vectors), len(chunks)
                    )
                # 4. Save chunks + vectors
                db.add_all(
                    Chunk(
                        document_id=document.id,
                        page_number=chunk.page_number,
                        content=chunk.content,
                        embedding=vector,
                    )
                    for chunk, vector in zip(chunks, vectors)
                )
                document.status = DocumentStatus.READY
            db.commit()
            logger.info(
                "Document %s: %s in %.0fs",
                document_id, document.status, time.monotonic() - started,
            )
        except Exception:
            logger.exception("Processing failed for document %s", document_id)
            db.rollback()  # throw away any half-saved chunks
            document = db.get(Document, document_id)
            if document is not None:
                document.status = DocumentStatus.FAILED
                db.commit()
    finally:
        db.close()
        if path is not None:
            path.unlink(missing_ok=True)


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

    # 4. Check the number of pages (long PDFs take too long to process on a small server)
    page_count = count_pages(bytes(data))
    if page_count is None:
        raise HTTPException(status_code=400, detail="This PDF couldn't be opened")
    if page_count > settings.max_pdf_pages:
        raise HTTPException(
            status_code=413,
            detail=f"This PDF has {page_count} pages; the limit is {settings.max_pdf_pages}",
        )

    # 5. Save the document row first, so we get an id to name the file with
    document = Document(
        user_id=current_user.id,
        filename=filename[:255],
        size_kb=max(1, round(len(data) / 1024)),
        status=DocumentStatus.PROCESSING,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    # 6. Save the PDF to disk (only until it has been processed)
    path = pdf_path(document)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)

    # 7. Read the text after the response is sent, so the upload feels fast
    background_tasks.add_task(process_document, document.id)
    return document


@router.get("", response_model=list[DocumentOut])
def list_documents(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.scalars(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.uploaded_at.desc())
    ).all()


@router.post("/search", response_model=list[SearchResult])
def search_documents(
    body: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Find the chunks most relevant to a question (no AI answer yet, just the matches)."""
    if body.document_ids:
        # Every requested document must exist and belong to this user
        owned_ids = set(
            db.scalars(
                select(Document.id).where(
                    Document.id.in_(body.document_ids), Document.user_id == current_user.id
                )
            )
        )
        if owned_ids != set(body.document_ids):
            raise HTTPException(status_code=404, detail="Document not found")

    results = search_chunks(
        db, current_user.id, body.question, body.document_ids, body.top_k
    )
    return [
        SearchResult(
            chunk_id=r.chunk_id,
            document_id=r.document_id,
            document=r.filename,
            page=r.page_number,
            content=r.content,
            score=r.score,
        )
        for r in results
    ]


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
    db.delete(document)  # the database also deletes its chunks (ON DELETE CASCADE)
    db.commit()
