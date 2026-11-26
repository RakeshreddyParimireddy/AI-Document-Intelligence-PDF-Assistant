"""Insight routes: summarize a document, extract fields from it, and dashboard stats."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Chat, Document, DocumentStatus, Message, Summary, User
from app.routers.documents import get_own_document, pdf_path
from app.schemas import DashboardStats, ExtractOut, ExtractRequest, ExtractedFieldOut, SummaryOut
from app.services import llm
from app.services.pdf_reader import extract_pages

router = APIRouter(prefix="/api", tags=["insights"])


def get_ready_document(document_id: int, user: User, db: Session) -> Document:
    document = get_own_document(document_id, user, db)
    if document.status != DocumentStatus.READY:
        raise HTTPException(status_code=409, detail="The document is not ready yet")
    return document


def read_document_text(document: Document) -> tuple[str, str | None]:
    """Return the document text (with page markers) and a note if it had to be shortened."""
    pages = [(p.page_number, p.text) for p in extract_pages(str(pdf_path(document))) if p.text]
    text, pages_used = llm.format_document(pages)
    note = None
    if pages_used < len(pages):
        note = (
            f"This document is very long, so only the first {pages_used} of "
            f"{len(pages)} pages with text were read."
        )
    return text, note


def run_llm(task):
    """Run an LLM task and turn its errors into clear HTTP errors."""
    try:
        return task()
    except llm.LLMNotConfiguredError:
        raise HTTPException(
            status_code=503, detail="The AI is not configured: set LLM_API_KEY in .env"
        )
    except llm.LLMServiceError:
        raise HTTPException(status_code=502, detail="The AI service failed. Please try again.")


# ---------- Summary ----------
@router.get("/documents/{document_id}/summary", response_model=SummaryOut)
def get_summary(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The saved summary, if one was made before (no AI call, free)."""
    document = get_own_document(document_id, current_user, db)
    summary = db.scalar(select(Summary).where(Summary.document_id == document.id))
    if summary is None:
        raise HTTPException(status_code=404, detail="No summary yet")
    return summary


@router.post("/documents/{document_id}/summarize", response_model=SummaryOut)
def summarize(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Make a new summary + key points with the AI (replaces any previous one)."""
    document = get_ready_document(document_id, current_user, db)
    text, note = read_document_text(document)
    result = run_llm(lambda: llm.summarize_document(document.filename, text))

    summary_text = f"{result.summary}\n\n({note})" if note else result.summary
    summary = db.scalar(select(Summary).where(Summary.document_id == document.id))
    if summary is None:
        summary = Summary(document_id=document.id, summary=summary_text, key_points=result.key_points)
        db.add(summary)
    else:
        summary.summary = summary_text
        summary.key_points = result.key_points
        summary.created_at = func.now()
    db.commit()
    db.refresh(summary)
    return summary


# ---------- Extraction ----------
@router.post("/documents/{document_id}/extract", response_model=ExtractOut)
def extract(
    document_id: int,
    body: ExtractRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Find the requested fields (e.g. "invoice date", "total amount") in the document."""
    document = get_ready_document(document_id, current_user, db)
    # Remove duplicates ("Total" and "total" count as the same), keep the order
    fields, seen = [], set()
    for field in body.fields:
        if field.lower() not in seen:
            seen.add(field.lower())
            fields.append(field)
    text, note = read_document_text(document)
    results = run_llm(lambda: llm.extract_fields(document.filename, text, fields, document.pages))
    return ExtractOut(
        document_id=document.id,
        results=[ExtractedFieldOut(field=r.field, value=r.value, page=r.page) for r in results],
        note=note,
    )


# ---------- Dashboard ----------
@router.get("/dashboard/stats", response_model=DashboardStats)
def dashboard_stats(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    documents = db.scalar(
        select(func.count()).select_from(Document).where(Document.user_id == current_user.id)
    )
    # Pages of documents that finished processing successfully
    pages_processed = db.scalar(
        select(func.coalesce(func.sum(Document.pages), 0)).where(
            Document.user_id == current_user.id, Document.status == DocumentStatus.READY
        )
    )
    # Every question = one "user" message in one of this user's chats
    questions_asked = db.scalar(
        select(func.count())
        .select_from(Message)
        .join(Chat, Message.chat_id == Chat.id)
        .where(Chat.user_id == current_user.id, Message.role == "user")
    )
    return DashboardStats(
        documents=documents, pages_processed=pages_processed, questions_asked=questions_asked
    )
