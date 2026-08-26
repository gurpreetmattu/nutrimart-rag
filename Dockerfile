# --- Stage 1: build the React frontend ---
FROM node:20-slim AS frontend-build
WORKDIR /frontend
COPY frontend-react/package.json frontend-react/package-lock.json ./
RUN npm ci
COPY frontend-react/ ./
RUN npm run build

# --- Stage 2: Python runtime ---
FROM python:3.11-slim
WORKDIR /app

# Unbuffered stdout/stderr — without this, Python's output only flushes
# once the buffer fills or the process exits, which on a PaaS host with no
# real terminal attached means the platform's log viewer shows NOTHING
# while a slow step is in progress (confirmed real: a Render deploy showed
# a 5+ minute total blackout between "Deploying..." and a port-scan
# timeout, with zero visibility into what the process was actually doing
# — turned out to be the model-download issue this same commit fixes, but
# the silence itself made that much harder to diagnose than it needed to
# be).
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# CPU-only torch, installed explicitly BEFORE the rest of requirements.txt
# so pip's resolver sees it already satisfied and never pulls the default
# CUDA-enabled Linux wheel — confirmed real: that default build is
# needlessly heavy on both image size and runtime RAM for a container that
# has no GPU at all, and was a real contributing factor to an OOM kill on
# Render's free tier (512MB RAM cap). The CPU wheel is a meaningful chunk
# smaller and lighter at import/inference time.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
COPY data/ data/
COPY --from=frontend-build /frontend/dist/ frontend-react/dist/

# products.sqlite is deterministic, offline-derivable data — built once at
# image-build time so a container never needs to run ingestion itself.
# Qdrant is a separate, stateful service this image does NOT embed — see
# README's Deploy section for why (a managed Qdrant, e.g. Qdrant Cloud's
# free tier, is the intended target) and for the one-time
# embed_and_upsert.py step that must be run against it before first use.
RUN python src/ingestion/load_products.py data/raw db

# Pre-download the embedding model and cross-encoder at BUILD time, not
# runtime. Without this, api/resources.py's first-request model load pulls
# ~130MB+ from Hugging Face Hub over whatever network the deploy host has
# — confirmed real on Render's free tier: this either stalled outright or
# was slow enough that the container never bound its port within Render's
# ~5-minute scan window, and the deploy was killed before ever starting
# uvicorn. Baking the weights into the image means a cold start never
# depends on Hugging Face's availability/speed at all, on any host.
RUN python -c "\
from sentence_transformers import SentenceTransformer, CrossEncoder; \
SentenceTransformer('BAAI/bge-small-en-v1.5'); \
CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')"

# Railway/Render/most PaaS targets inject $PORT at runtime — main.py serves
# both the built frontend and /api/*, so this is the one process a typical
# single-service deploy needs. To deploy api/main_langchain.py instead (the
# no-frontend, +observability API on its own service), override this
# image's start command in your host's service settings rather than
# rebuilding the image — see README's Deploy section.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --app-dir src"]
