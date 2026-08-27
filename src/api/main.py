"""
api/main.py — the HTTP layer: FastAPI app serving the built
frontend-react/ production bundle (frontend-react/dist), talking to the
RAG pipeline underneath.

Does not reimplement any pipeline logic — every /api/chat call goes
through the exact same ask_langchain_hybrid.ask()/classify_query() code
path `python src/ask_langchain_hybrid.py "..."` uses, just with the heavy
models (embedding model, Qdrant client, BM25 index, cross-encoder)
preloaded once at startup via api/resources.py instead of reloaded per
call. See ask_langchain_hybrid.py's own module docstring for what's
LangChain-native vs. plain Python.

Run with:
    cd frontend-react && npm run build   # rebuild dist/ after any frontend change
    uvicorn api.main:app --reload --app-dir src

For frontend development with hot reload instead, run
`npm run dev` in frontend-react/ (proxies /api to this server on :8000 —
see frontend-react/vite.config.js) and use that dev server's URL instead.
"""
import json
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from config import get_sqlite_conn
from routing.query_router import classify_query
from ask_langchain_hybrid import ask as ask_langchain_hybrid, INSUFFICIENT_EVIDENCE_MESSAGE
from api.resources import get_resources
from api.response_helpers import Source, _confidence, _build_sources
from api.security import check_rate_limit, detect_prompt_injection
from api.session_store import get_session, save_session
from api.auth import router as auth_router
from api.orders import router as orders_router
from conversation.resolve import resolve_followup
from conversation.state import set_product, default_state
from generation.consumer_view import to_consumer_friendly
from eval.faithfulness_score import faithfulness_score
from structured.users import init_users_table
from structured.orders import init_orders_tables

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend-react" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Loads the embedding model / Qdrant client / BM25 index / cross-encoder
    # once, up front, rather than paying that cost on the first request.
    get_resources()
    conn = get_sqlite_conn()
    try:
        init_users_table(conn)
        init_orders_tables(conn)
    finally:
        conn.close()
    yield


app = FastAPI(title="Quick-Commerce RAG API", lifespan=lifespan)
app.include_router(auth_router)
app.include_router(orders_router)


class ChatRequest(BaseModel):
    # Bounds, not just a type — an unbounded query becomes an unbounded
    # prompt (real cost/quota vector, see api/security.py's docstring).
    # 1000 chars is generous for a genuine question against this KB (the
    # longest real question in eval/test_questions.py is well under 200).
    query: str = Field(min_length=1, max_length=1000)
    product_id: str | None = None
    # Additive, backward compatible: omitting this means no conversation
    # memory (every existing caller before this session behaves exactly
    # as before). See api/session_store.py.
    session_id: str | None = None


class ConfidenceBreakdown(BaseModel):
    retrieval_relevance: float | None = None
    entity_match: bool = False
    evidence_completeness: bool = False
    claim_support: float | None = None


class ChatResponse(BaseModel):
    # Consumer-facing by default (technical evidence invisible by default,
    # not deleted) — generation/consumer_view.py's
    # stripped text, no [TAG] markers or inline citations.
    answer: str
    # The full, unmodified typed-claim/cited text `answer` was derived
    # from — same content the pre-this-session `answer` field always was.
    # Kept for an optional "why this answer?" technical view; not shown
    # by default.
    answer_technical: str
    route: str
    product_id: str | None = None
    sources: list[Source] = []
    confidence: str = "medium"
    top_score: float | None = None
    confidence_breakdown: ConfidenceBreakdown | None = None
    # Best-effort flag only (see api/security.py::detect_prompt_injection's
    # docstring) — surfaced so a caller/UI CAN show a subtle notice, but
    # the request is still answered normally either way. This is not a
    # hard block: false positives on legitimate food-safety questions
    # ("ignore what the label says") are a real risk with a hard block,
    # and generation/llm.py's SYSTEM_PROMPT is the actual structural
    # defense (context-only answers, typed claims) either way.
    injection_flagged: bool = False


def _row_to_summary(row) -> dict:
    pack = json.loads(row["pack_size_json"] or "{}")
    return {
        "product_id": row["product_id"],
        "name": row["name"],
        "brand": row["brand"],
        "category": row["category"],
        "pack_size": pack,
    }


def _row_to_detail(row) -> dict:
    summary = _row_to_summary(row)
    nutrition = json.loads(row["nutrition_json"] or "{}")
    summary.update({
        "description": row["description"],
        "ingredients_raw": row["ingredients_raw"],
        "allergens_contains": json.loads(row["allergens_contains_json"] or "[]"),
        "allergens_may_contain": json.loads(row["allergens_may_contain_json"] or "[]"),
        "nutrition": nutrition,
        "fssai_license": row["fssai_license"],
        "co_licensee_fssai": row["co_licensee_fssai"],
    })
    return summary


@app.get("/api/products")
def list_products():
    conn = get_sqlite_conn()
    rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    conn.close()
    return [_row_to_summary(r) for r in rows]


@app.get("/api/products/{product_id}")
def get_product(product_id: str):
    conn = get_sqlite_conn()
    row = conn.execute("SELECT * FROM products WHERE product_id = ?", (product_id,)).fetchone()
    conn.close()
    if row is None:
        raise HTTPException(status_code=404, detail=f"No product '{product_id}'")
    return _row_to_detail(row)


def _confidence_breakdown(route: str, chunks: list[dict] | None, answer_technical: str) -> ConfidenceBreakdown:
    """
    One opaque confidence number isn't as useful as seeing what it's
    actually made of. Reuses eval/faithfulness_score.py's
    faithfulness_score() directly for claim_support rather than a second
    implementation — the same function generation/groundedness.py's
    annotation pass already computes as a side effect.
    """
    checked, flagged = faithfulness_score(answer_technical, chunks or [])
    is_sql_route = route in ("product_fact", "product_comparison")
    return ConfidenceBreakdown(
        retrieval_relevance=round(chunks[0]["rerank_score"], 3) if chunks else None,
        entity_match=is_sql_route or bool(chunks),
        evidence_completeness=bool(chunks) or is_sql_route,
        claim_support=round((checked - flagged) / checked, 3) if checked else None,
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request):
    # Rate-limited specifically because this is the one endpoint that
    # spends real LLM-provider quota per call — /api/products is plain
    # SQLite reads with no such cost. See api/security.py's docstring:
    # this project hit real quota exhaustion multiple times in one day
    # from its own testing traffic alone — an unrated public endpoint
    # risks the same from a handful of page refreshes.
    client_id = request.client.host if request.client else "unknown"
    allowed, retry_after = check_rate_limit(client_id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded — try again in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

    injection_flagged = detect_prompt_injection(req.query)

    # `state` is ephemeral (not saved back) when no session_id is given —
    # every pre-this-session caller (or a fresh curl call) still gets a
    # perfectly normal single-turn answer, just without memory across
    # requests. conversation/resolve.py handles a state with no
    # product_id/known_facts set exactly like it always handled a bare
    # query — see its docstring.
    state = get_session(req.session_id) if req.session_id else default_state()

    conn = get_sqlite_conn()
    if req.product_id:
        row = conn.execute("SELECT name FROM products WHERE product_id = ?", (req.product_id,)).fetchone()
        if row is not None:
            set_product(state, req.product_id, row["name"])
    conn.close()

    # resolve_followup() runs here ONLY to compute route/product_id for the
    # response metadata below — ask_langchain_hybrid() gets the RAW req.query and
    # resolves it itself internally (it always does, whenever
    # conversation_state is not None, which it always is on this path).
    # Passing the already-resolved text into ask_langchain_hybrid() used to run
    # resolve_followup() a second time on top of its own output — confirmed
    # real 2026-08-21: a fact-led anaphora rewrite like "Is 43.0g of total
    # sugars a lot? Is that too much?" got re-resolved into "For Amul Dark
    # Chocolate: Is 43.0g of total sugars a lot? Is that too much?", which
    # re-prepends the product name — exactly the phrasing
    # conversation/resolve.py's own docstring documents as a verified,
    # deliberately-avoided regression (drags the cross-encoder toward
    # product/ingredient chunks over generic guidance chunks). Every
    # follow-up question hitting the real server was silently getting this
    # worse, double-resolved phrasing; ask_langchain_hybrid() called directly (every
    # eval script, CLI, and today's manual verification) never had this bug
    # since none of those pass an already-resolved query back in.
    resolved_query = resolve_followup(req.query, state)
    conn = get_sqlite_conn()
    route = classify_query(resolved_query, conn)
    conn.close()

    resources = get_resources()
    answer_technical, chunks = ask_langchain_hybrid(
        req.query, verbose=False, resources=resources, return_chunks=True, conversation_state=state,
    )
    if req.session_id:
        save_session(req.session_id, state)

    # Route reporting derived from what ask_langchain_hybrid() actually
    # did this turn, not a second speculative classification call.
    # classify_query() above still tells us definitively when the cheap
    # deterministic product_fact fast path fired; otherwise, chunks is
    # None exactly when ask_langchain_hybrid()'s tool-calling loop answered entirely
    # from structured tools (product fact/ingredient/allergen/comparison)
    # with no knowledge-base retrieval — the same case the old
    # "product_comparison" label covered, just derived from the real
    # outcome instead of a guess made before the call even ran.
    if route.route == "product_fact":
        reported_route = "product_fact"
    elif chunks is None and answer_technical != INSUFFICIENT_EVIDENCE_MESSAGE:
        reported_route = "product_comparison"
    else:
        # Either real chunks came back (KB retrieval happened), or chunks
        # is None because nothing could be answered at all — the latter
        # must NOT be labeled "product_comparison" (that maps to
        # _confidence()'s "instant" tier, which would show a false-
        # confident badge on a genuine [UNCERTAIN] insufficient-evidence
        # answer). Confirmed real bug caught during the 2026-08-21
        # tool-calling migration, before it ever shipped.
        reported_route = "retrieval"

    sources = _build_sources(answer_technical, chunks)
    confidence, top_score = _confidence(reported_route, chunks)
    confidence_breakdown = _confidence_breakdown(reported_route, chunks, answer_technical)

    return ChatResponse(
        answer=to_consumer_friendly(answer_technical), answer_technical=answer_technical,
        route=reported_route, product_id=route.product_id or state.get("product_id"), sources=sources,
        confidence=confidence, top_score=top_score, confidence_breakdown=confidence_breakdown,
        injection_flagged=injection_flagged,
    )


# Mounted last so it only catches requests the /api/* routes above didn't.
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
