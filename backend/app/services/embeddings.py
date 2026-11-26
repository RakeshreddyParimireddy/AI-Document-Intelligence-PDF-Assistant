"""Turn text into vectors ("embeddings") that capture its meaning.

Uses a small free model that runs on the CPU, no API key needed.
Texts with similar meaning get vectors that point in a similar direction.
"""
from functools import lru_cache

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # length of each vector this model produces (must match the chunks table)


@lru_cache
def get_model() -> SentenceTransformer:
    # Loaded once, on first use, then reused (loading takes a few seconds)
    return SentenceTransformer(MODEL_NAME, device="cpu")


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed many texts at once (faster than one by one)."""
    if not texts:
        return []
    # normalize_embeddings=True makes every vector length 1, so cosine similarity works well
    vectors = get_model().encode(texts, batch_size=32, normalize_embeddings=True)
    return vectors.tolist()


def embed_text(text: str) -> list[float]:
    """Embed a single text (e.g. a user's question)."""
    return embed_texts([text])[0]
