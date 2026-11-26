"""Turn text into vectors ("embeddings") that capture its meaning.

Uses a small free model that runs on the CPU, no API key needed.
Texts with similar meaning get vectors that point in a similar direction.
"""
import threading

from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # length of each vector this model produces (must match the chunks table)

_model: SentenceTransformer | None = None
_model_lock = threading.Lock()


def get_model() -> SentenceTransformer:
    """Load the model once, then reuse it (loading takes a few seconds).

    The lock matters: if two requests load the model at the same moment
    (e.g. two uploads right after startup), the loading crashes.
    """
    global _model
    with _model_lock:
        if _model is None:
            _model = SentenceTransformer(MODEL_NAME, device="cpu")
    return _model


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
