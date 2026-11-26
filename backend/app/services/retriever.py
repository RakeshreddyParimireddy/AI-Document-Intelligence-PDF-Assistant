"""Vector search: find the chunks whose meaning is closest to a question."""
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models import Chunk, Document, DocumentStatus
from app.services.embeddings import embed_text


@dataclass
class RetrievedChunk:
    chunk_id: int
    document_id: int
    filename: str
    page_number: int
    content: str
    score: float  # cosine similarity: 1.0 = same meaning, around 0 = unrelated


def search_chunks(
    db: Session,
    user_id: int,
    question: str,
    document_ids: list[int] | None = None,
    top_k: int = 5,
) -> list[RetrievedChunk]:
    """Return the `top_k` chunks most similar to the question.

    Only searches the user's own READY documents (optionally only `document_ids`).
    """
    question_vector = embed_text(question)
    # Cosine distance: 0 = identical meaning, 2 = opposite. Smaller is better.
    distance = Chunk.embedding.cosine_distance(question_vector)

    query = (
        select(Chunk, Document.filename, distance.label("distance"))
        .join(Document, Chunk.document_id == Document.id)
        .where(Document.user_id == user_id, Document.status == DocumentStatus.READY)
        .order_by(distance)
        .limit(top_k)
    )
    if document_ids:
        query = query.where(Document.id.in_(document_ids))

    # The fast vector index looks at a limited number of candidates and then applies
    # our filters (this user, these documents). "iterative_scan" tells it to keep
    # looking until it finds enough matches, so filtering never hides results.
    db.execute(text("SET LOCAL hnsw.iterative_scan = relaxed_order"))
    rows = db.execute(query).all()

    results = [
        RetrievedChunk(
            chunk_id=chunk.id,
            document_id=chunk.document_id,
            filename=filename,
            page_number=chunk.page_number,
            content=chunk.content,
            score=round(1 - dist, 4),
        )
        for chunk, filename, dist in rows
    ]
    # relaxed_order can be very slightly out of order, so sort once more to be exact
    return sorted(results, key=lambda r: r.score, reverse=True)
