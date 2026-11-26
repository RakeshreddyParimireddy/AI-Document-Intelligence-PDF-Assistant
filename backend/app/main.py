"""FastAPI entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import models  # noqa: F401  (imported so its tables are registered on Base)
from app.database import Base, engine
from app.routers import auth, chat, documents
from app.services.embeddings import get_model


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create any missing tables when the app starts
    Base.metadata.create_all(bind=engine)
    # Load the embedding model now, so the first upload/question isn't slow
    get_model()
    yield


app = FastAPI(title="DocuMind API", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)


@app.get("/api/health")
def health():
    """Checks that the API is running and can talk to the database."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            has_vector = conn.execute(
                text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
            ).scalar()
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "unavailable", "pgvector": False},
        )
    return {"status": "ok", "database": "connected", "pgvector": bool(has_vector)}
