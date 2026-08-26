"""
api/resources.py — loads the hybrid pipeline's heavy objects (embedding
model, Qdrant client, BM25 index, cross-encoder) exactly once at process
startup, instead of the per-call loading ask_hybrid.py's CLI/eval callers
do. A live API serving repeated requests can't afford to reload a
SentenceTransformer and rebuild the BM25 index on every single question.

Exposes get_resources(), which builds the bundle on first call and caches
it in a module-level global — src/api/main.py calls this once during its
FastAPI lifespan startup and passes the bundle into ask_hybrid()/
retrieve_hybrid_with_retry()'s new optional `resources` parameter.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentence_transformers import SentenceTransformer

from config import get_qdrant_client, EMBEDDING_MODEL
from retrieval.bm25_index import build_bm25_index
from retrieval.rerank import get_cross_encoder

_resources: dict | None = None


def get_resources() -> dict:
    global _resources
    if _resources is None:
        bm25_index, bm25_chunks = build_bm25_index(Path("data/raw"))
        _resources = {
            "dense_model": SentenceTransformer(EMBEDDING_MODEL),
            "qdrant_client": get_qdrant_client(),
            "bm25_index": bm25_index,
            "bm25_chunks": bm25_chunks,
            "cross_encoder": get_cross_encoder(),
        }
    return _resources
