"""FastAPI entry point."""
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.database import engine

app = FastAPI(title="DocuMind API")


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
