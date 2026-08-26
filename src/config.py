"""
config.py — shared constants for ingestion and retrieval scripts.

Lives at src/config.py (sibling to ingestion/, retrieval/, eval/) so both
sides can import it without a fragile cross-folder script import.
"""
import sqlite3
import sys
from pathlib import Path

from qdrant_client import QdrantClient

# Windows' default console codepage (cp1252) can't encode characters an LLM
# response may legitimately contain (em dashes, curly quotes, the non-
# breaking hyphen U+2011, etc.) — confirmed real crash 2026-08-20 printing
# a Groq-rewritten query from ask_hybrid.py's corrective-retry path. Every
# CLI entrypoint and the API server import this module, so reconfiguring
# stdout/stderr here once covers all of them instead of patching each
# script's __main__ block separately. Guarded in a try/except: some stream
# types (e.g. under certain test runners or redirected output) don't
# support reconfigure(), and this must never be the reason a script fails.
if sys.platform == "win32":
    for _stream in (sys.stdout, sys.stderr):
        try:
            _stream.reconfigure(encoding="utf-8")
        except (AttributeError, ValueError):
            pass

COLLECTION_NAME = "kb_baseline"
EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIM = 384  # bge-small's output dimension — must match collection config
QDRANT_HOST = "localhost"
QDRANT_PORT = 6333

# src/config.py -> parent is src/, parent.parent is the project root
DB_PATH = Path(__file__).resolve().parent.parent / "db" / "products.sqlite"

# bge models expect this instruction prefix on the QUERY side only, not on
# documents. Omitting this measurably hurts bge retrieval quality — it's a
# documented model requirement, not a retrieval-strategy choice, so it's
# kept even in the deliberately-naive baseline.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def get_sqlite_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
