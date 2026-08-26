"""
bm25_index.py — sparse (BM25) side of the hybrid retriever
(retrieval/search_hybrid.py). Dense-only was the deliberate Phase 3
baseline limitation; this is the Phase 5 fix.

Builds an in-memory index over the same chunk set embed_and_upsert.py
puts in Qdrant (~120 chunks total), so it's cheap enough to rebuild per
process rather than persist — no index file, no caching layer. A CLI
call rebuilds it once per invocation; api/resources.py builds it once and
caches it for the life of the server process instead.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from rank_bm25 import BM25Okapi

from ingestion.parse_kb import Chunk, parse_all_kb_files

TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(text.lower())


def build_bm25_index(raw_dir: Path) -> tuple[BM25Okapi, list[Chunk]]:
    chunks = parse_all_kb_files(raw_dir)
    tokenized_corpus = [_tokenize(c.text) for c in chunks]
    index = BM25Okapi(tokenized_corpus)
    return index, chunks


def bm25_search(index: BM25Okapi, chunks: list[Chunk], query: str, top_n: int = 20) -> list[tuple[Chunk, float]]:
    scores = index.get_scores(_tokenize(query))
    ranked = sorted(zip(chunks, scores), key=lambda pair: pair[1], reverse=True)
    return ranked[:top_n]


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "is aspartame safe in Diet Coke"
    raw_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/raw")

    index, chunks = build_bm25_index(raw_dir)
    results = bm25_search(index, chunks, query, top_n=5)

    print(f"Query: {query!r}\n{'-'*60}")
    for chunk, score in results:
        print(f"[{score:.3f}] {chunk.source_file} — {chunk.heading}")
