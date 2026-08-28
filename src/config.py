"""
config.py — shared constants for ingestion and retrieval scripts.

Lives at src/config.py (sibling to ingestion/, retrieval/, eval/) so both
sides can import it without a fragile cross-folder script import.
"""
import os
import sqlite3
import sys
from pathlib import Path

import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from qdrant_client import QdrantClient

# Every ask_*.py/api/main*.py entrypoint already calls load_dotenv() itself
# before importing this module — but a CLI script that only needs
# ingestion/DB constants (ingestion/embed_and_upsert.py, load_products.py)
# never did, since QDRANT_HOST/PORT never needed .env before QDRANT_URL/
# QDRANT_API_KEY existed. Confirmed real: embed_and_upsert.py silently read
# an unset QDRANT_URL and fell back to localhost, ingesting into the wrong
# (local) Qdrant instance instead of the cloud one actually configured in
# .env. Loading it here, once, guarantees every current and future consumer
# of this module sees .env's values regardless of whether its own entrypoint
# remembers to call load_dotenv() first — a second load_dotenv() call
# upstream is a harmless no-op (it doesn't override already-set values).
load_dotenv()

# Windows' default console codepage (cp1252) can't encode characters an LLM
# response may legitimately contain (em dashes, curly quotes, the non-
# breaking hyphen U+2011, etc.) — confirmed real crash 2026-08-20 printing
# a Groq-rewritten query from the hybrid pipeline's corrective-retry path. Every
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

# Local dev default (docker-compose's qdrant service) stays a bare host/port
# pair with no auth, unchanged from before. A deployed environment (Cloud
# Run, Qdrant Cloud, any managed instance) instead sets QDRANT_URL — a full
# https://... URL, optionally with QDRANT_API_KEY — since a managed instance
# is never reachable at "localhost" and almost always requires an API key.
# get_qdrant_client() below picks whichever is configured; nothing changes
# for an existing local setup that never sets QDRANT_URL.
QDRANT_HOST = os.environ.get("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.environ.get("QDRANT_PORT", "6333"))
QDRANT_URL = os.environ.get("QDRANT_URL")
QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY")

# src/config.py -> parent is src/, parent.parent is the project root. The
# Dockerfile builds products.sqlite into the image at that default path, so
# a deployed environment normally never needs to set this — DB_PATH exists
# for the rarer case of pointing at a separately-mounted/persistent path
# instead. See README's Deploy section.
DB_PATH = Path(os.environ.get("DB_PATH", str(Path(__file__).resolve().parent.parent / "db" / "products.sqlite")))

# users/orders/order_items live here, NOT in products.sqlite — Cloud Run
# (this project's deploy target) runs with min-instances=0, so a
# container's local filesystem (including a SQLite file baked into the
# image) does not survive scale-to-zero: every signup/order written to it
# vanished the moment the next request cold-started a fresh container from
# the image. Confirmed as the real cause of a live "works right after
# signup, 'invalid password' 10-15 minutes later" report — not an auth bug,
# a storage-durability bug. products.sqlite itself is unaffected by this
# (it's read-only, deterministic, rebuilt into every image at build time,
# so a fresh container always has the right product data) — only the
# tables an actual user writes to at runtime needed to move off local
# disk. The default here matches the docker-compose `postgres` service for
# local dev; a deployed environment sets DATABASE_URL to a managed
# instance (Supabase's free tier) instead, same QDRANT_URL/QDRANT_HOST
# pattern used above. Deliberately no SQLite fallback for these tables —
# that would silently reintroduce the exact bug this exists to fix.
DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql://nutrimart:nutrimart@localhost:5432/nutrimart"
)

# bge models expect this instruction prefix on the QUERY side only, not on
# documents. Omitting this measurably hurts bge retrieval quality — it's a
# documented model requirement, not a retrieval-strategy choice, so it's
# kept even in the deliberately-naive baseline.
BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def get_qdrant_client() -> QdrantClient:
    if QDRANT_URL:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def get_sqlite_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_pg_conn() -> psycopg.Connection:
    # dict_row so callers can keep the same row["field"] access pattern
    # get_sqlite_conn()'s sqlite3.Row already gave them — no call-site
    # changes needed beyond the ? -> %s placeholder swap SQL itself needs.
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)
