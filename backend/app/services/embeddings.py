"""Turn text into vectors ("embeddings") that capture its meaning.

Uses a small free model (all-MiniLM-L6-v2) that runs on the CPU, no API key needed.
Texts with similar meaning get vectors that point in a similar direction.

It runs with fastembed (ONNX Runtime) instead of PyTorch: same model, same vectors,
but it needs far less memory, so the backend fits in a 512 MB free hosting plan.
"""
import os
import threading

from fastembed import TextEmbedding

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # length of each vector this model produces (must match the chunks table)

# Texts embedded together in one step. Bigger is a little faster but uses much more memory:
# 32 at a time peaked at ~570 MB, 8 at a time at ~385 MB (measured with a 300-chunk PDF).
BATCH_SIZE = 8

# CPU threads used for embedding. Inside Docker the app sees ALL of the computer's cores,
# even when the host allows only a slice of one (Render free = 0.1 CPU). Many threads
# fighting over that slice slow everything down badly, so we use one.
EMBEDDING_THREADS = 1

# Where the model files are stored. The Docker image downloads them here at build time.
MODEL_CACHE_DIR = os.environ.get("FASTEMBED_CACHE_PATH")

_model: TextEmbedding | None = None
_model_lock = threading.Lock()


def get_model() -> TextEmbedding:
    """Load the model once, then reuse it (loading takes a few seconds).

    The lock matters: two requests must not load the model at the same moment.
    """
    global _model
    with _model_lock:
        if _model is None:
            _model = TextEmbedding(MODEL_NAME, cache_dir=MODEL_CACHE_DIR, threads=EMBEDDING_THREADS)
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed many texts. Every vector has length 1, so cosine similarity works well."""
    if not texts:
        return []
    # No lock here: uploads are already processed one at a time (see documents.py), and a
    # user's question must never wait for an upload - it only shares the CPU with it.
    # (A lock here made questions wait minutes: Python locks don't take turns fairly.)
    return [vector.tolist() for vector in get_model().embed(texts, batch_size=BATCH_SIZE)]


def embed_text(text: str) -> list[float]:
    """Embed a single text (e.g. a user's question)."""
    return embed_texts([text])[0]
