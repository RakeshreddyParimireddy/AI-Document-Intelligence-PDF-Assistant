"""Insight routes. For now: dashboard stats. (Summarize + extract come in milestone 10.)"""
from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Chat, Document, DocumentStatus, Message, User
from app.schemas import DashboardStats

router = APIRouter(prefix="/api", tags=["insights"])


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
