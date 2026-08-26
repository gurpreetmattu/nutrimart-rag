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

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

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

# Railway (and most PaaS targets) inject $PORT at runtime — main.py serves
# both the built frontend and /api/*, so this is the one process a typical
# single-service Railway deploy needs. To deploy api/main_langchain.py
# instead (the no-frontend, +observability API on its own service), override
# this image's start command in Railway's service settings rather than
# rebuilding the image — see README's Deploy section.
EXPOSE 8000
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --app-dir src"]
