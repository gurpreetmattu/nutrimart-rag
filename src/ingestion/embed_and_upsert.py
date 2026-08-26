"""
embed_and_upsert.py — embeds KB chunks with bge-small and upserts to Qdrant.

Baseline (Phase 3) design choices, deliberate:
- ONE flat collection, no doc_type-scoped sub-collections. Phase 5's hybrid
  pipeline is where metadata-scoped retrieval gets introduced — the whole
  point of the baseline is to NOT have that yet, so the eval table in
  Phase 7 can show the improvement it provides.
- doc_type and entity are still stored as Qdrant payload fields even though
  the baseline retriever won't filter on them — this avoids a second
  re-embedding pass later; Phase 5 can start filtering immediately using
  data that's already there.
"""
import sys
from pathlib import Path

# Add src/ to sys.path so `config` (one level up) is importable regardless
# of which directory this script is run from.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer

from config import COLLECTION_NAME, EMBEDDING_MODEL, EMBEDDING_DIM, QDRANT_HOST, QDRANT_PORT, QDRANT_URL, get_qdrant_client
from parse_kb import parse_all_kb_files, Chunk


def ensure_collection(client: QdrantClient, recreate: bool = True) -> None:
    """
    recreate=True drops and recreates the collection every run — fine for
    a baseline you're actively iterating on. Set False once you don't want
    to re-embed everything on every run.
    """
    if recreate and client.collection_exists(COLLECTION_NAME):
        client.delete_collection(COLLECTION_NAME)

    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE),
        )


def embed_and_upsert(chunks: list[Chunk], client: QdrantClient, model: SentenceTransformer) -> int:
    texts = [c.text for c in chunks]

    # bge models are trained with a specific instruction prefix for queries
    # (not for documents) — see search_baseline.py for the query-side prefix.
    # Documents are embedded as-is.
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    points = [
        PointStruct(
            id=i,
            vector=embeddings[i].tolist(),
            payload={
                "chunk_id": c.chunk_id,
                "source_file": c.source_file,
                "heading": c.heading,
                "text": c.text,
                "doc_type": c.doc_type,
                "entity": c.entity,
                "ins_no": c.ins_no,
                "comparison_group": c.comparison_group,
            },
        )
        for i, c in enumerate(chunks)
    ]

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


if __name__ == "__main__":
    raw_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")

    print(f"Parsing KB files from {raw_dir}...")
    chunks = parse_all_kb_files(raw_dir)
    print(f"Total chunks to embed: {len(chunks)}")

    print(f"\nLoading embedding model ({EMBEDDING_MODEL})... this downloads ~130MB on first run.")
    model = SentenceTransformer(EMBEDDING_MODEL)

    print(f"\nConnecting to Qdrant at {QDRANT_URL or f'{QDRANT_HOST}:{QDRANT_PORT}'}...")
    client = get_qdrant_client()
    ensure_collection(client, recreate=True)

    print(f"\nEmbedding and upserting {len(chunks)} chunks...")
    n = embed_and_upsert(chunks, client, model)

    print(f"\nDone. {n} points in collection '{COLLECTION_NAME}'.")
    print(f"Check the dashboard: http://localhost:6333/dashboard#/collections/{COLLECTION_NAME}")