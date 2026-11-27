FROM python:3.12-slim

WORKDIR /app

# Where the embedding model is stored (inside /app, so the non-root user below can read it)
ENV FASTEMBED_CACHE_PATH=/app/.cache/fastembed

# Install Python packages (cached unless the requirements files change)
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Download the embedding model now, so the app doesn't download it on every start
RUN python -c "from fastembed import TextEmbedding; TextEmbedding('sentence-transformers/all-MiniLM-L6-v2')"

COPY pytest.ini ./
COPY app ./app

# Run as a normal user, not root (safer)
RUN useradd --create-home --uid 1000 appuser \
    && mkdir -p uploads \
    && chown -R appuser /app
USER appuser

# Hosting sites like Render tell the app which port to use in $PORT; locally it's 8000.
# "exec" lets uvicorn receive the stop signal directly, so it shuts down cleanly.
EXPOSE 8000
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
