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
