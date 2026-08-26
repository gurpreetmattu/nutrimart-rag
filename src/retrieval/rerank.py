"""
rerank.py — cross-encoder reranking of hybrid-fused candidates
(retrieval/search_hybrid.py). Pipeline step 4 in project_state_summary.md:
"Cross-encoder reranking of top-k."

Cross-encoders score a (query, passage) pair directly rather than
comparing independently-embedded vectors, so they're the mechanism meant
to fix PHASE3_TESTING_LOG.md Finding 2 ("topically-adjacent-but-not-
responsive chunks crowd out the real answer") — a chunk can share a lot
of embedding-space similarity with the query while a cross-encoder still
correctly scores it as not actually answering the question.
"""
import sys
from math import exp
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sentence_transformers import CrossEncoder

RERANK_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"


def _sigmoid(x: float) -> float:
    return 1 / (1 + exp(-x))


def get_cross_encoder() -> CrossEncoder:
    return CrossEncoder(RERANK_MODEL)


def rerank(query: str, candidates: list[dict], cross_encoder: CrossEncoder, top_k: int = 5) -> list[dict]:
    """
    candidates: list of dicts with at least a "text" key (the chunk dict
    shape used throughout retrieval/). Returns the top_k candidates sorted
    by rerank_score descending, each with a "rerank_score" key added
    (sigmoid-normalized to ~0-1, since raw cross-encoder logits aren't
    otherwise interpretable as a corrective-retry threshold).
    """
    if not candidates:
        return []

    pairs = [(query, c["text"]) for c in candidates]
    raw_scores = cross_encoder.predict(pairs)

    for c, raw_score in zip(candidates, raw_scores):
        c["rerank_score"] = _sigmoid(float(raw_score))

    return sorted(candidates, key=lambda c: c["rerank_score"], reverse=True)[:top_k]
