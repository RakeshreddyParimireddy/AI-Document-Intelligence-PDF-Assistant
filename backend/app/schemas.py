"""Shapes of the data the API receives and returns (shared contract with the frontend)."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ---------- Auth ----------
class UserCreate(BaseModel):
    """Body of POST /api/auth/register (JSON)."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserOut(BaseModel):
    """A user as returned by the API (never includes the password)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime


class Token(BaseModel):
    """Response of POST /api/auth/login.

    Note: login takes FORM data (fields `username` = email, `password`),
    the standard OAuth2 format, so the "Authorize" button in /docs works.
    """
    access_token: str
    token_type: str = "bearer"


# ---------- Documents ----------
class DocumentOut(BaseModel):
    """A document as returned by the API.

    Upload is POST /api/documents/upload with multipart form field `file`.
    `status` is "processing" right after upload, then "ready" or "failed".
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    pages: int
    size_kb: int
    status: str
    uploaded_at: datetime


# ---------- Search (retrieval) ----------
class SearchRequest(BaseModel):
    """Body of POST /api/documents/search."""
    question: str = Field(min_length=1, max_length=1000)
    # Leave empty to search all your ready documents
    document_ids: list[int] | None = None
    top_k: int = Field(default=5, ge=1, le=20)


class SearchResult(BaseModel):
    """One matching chunk. `score` is similarity: higher = more relevant (max 1.0)."""
    chunk_id: int
    document_id: int
    document: str  # filename
    page: int
    content: str
    score: float


# ---------- Chat (RAG answers) ----------
class ChatCreate(BaseModel):
    """Body of POST /api/chats."""
    document_ids: list[int] = Field(min_length=1)
    title: str | None = Field(default=None, max_length=255)


class ChatOut(BaseModel):
    id: int
    title: str
    created_at: datetime
    document_ids: list[int]


class AskRequest(BaseModel):
    """Body of POST /api/chats/{id}/ask."""
    question: str = Field(min_length=1, max_length=1000)


class Citation(BaseModel):
    """Where part of an answer came from."""
    document_id: int
    document: str  # filename
    page: int
    snippet: str  # start of the chunk text used


class MessageOut(BaseModel):
    """A chat message. Assistant messages include `citations`."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    citations: list[Citation]
    created_at: datetime
