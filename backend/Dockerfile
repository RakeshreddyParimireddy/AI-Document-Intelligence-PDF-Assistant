FROM python:3.12-slim

WORKDIR /app

# Install the CPU-only version of PyTorch first (needed by sentence-transformers).
# The default version includes GPU (CUDA) files and is several GB bigger.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Install Python packages (cached unless the requirements files change)
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-dev.txt

# Download the embedding model now, so the app doesn't download it on first upload
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

COPY pytest.ini ./
COPY app ./app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
