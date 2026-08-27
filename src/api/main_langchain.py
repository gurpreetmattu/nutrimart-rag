"""
api/main_langchain.py — HTTP layer for ask_langchain_hybrid.py, mirroring
api/main.py's pattern (models/BM25 index/cross-encoder preloaded once at
startup instead of per-request) but as its own small app rather than a
change to api/main.py — that file also serves the built frontend-react/
bundle, and this one exists to expose extra observability endpoints
without touching that file's response shape. Preloading matters because a
cold, per-invocation reload of the embedding model, cross-encoder, and
BM25 index costs several real seconds of pure model-loading before a
query even starts.

Reuses api/resources.py::get_resources() directly rather than
ask_langchain_hybrid.py's own build_resources() — they build the exact
same dict shape (dense_model/qdrant_client/bm25_index/bm25_chunks/
cross_encoder), and api.resources already has the module-level caching
this file needs; duplicating that caching here would just be a second,
divergent copy. This also means the resource bundle is shared with
api/main.py's process if both ever ran together (they don't currently —
separate processes, separate ports — but the point stands: one cache, not
two).

Reuses api/security.py (rate limiting, prompt-injection flagging),
api/session_store.py (conversation memory), and generation/consumer_view.py
(stripped consumer-facing text) as-is — these are generic HTTP-layer
concerns unrelated to which pipeline answers the question, so duplicating
them here would be pure risk for no benefit.

Adds three fields api/main.py's ChatResponse doesn't have: `tool_trace`,
`timing`, `usage` — real per-request observability ask_langchain_hybrid.py
supports natively (see its own docstring). Left out of api/main.py's
response deliberately (scope creep on an unrelated file); included here
since this file's whole point is exposing what the pipeline is doing under
the hood.

Run with:
    uvicorn api.main_langchain:app --reload --app-dir src --port 8001
"""
import sys
from contextlib import asynccontextmanager
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

import json as _json

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from config import get_sqlite_conn
from ask_langchain_hybrid import ask, ask_stream, INSUFFICIENT_EVIDENCE_MESSAGE
from api.resources import get_resources
from api.response_helpers import Source, _confidence, _build_sources
from api.security import check_rate_limit, detect_prompt_injection
from api.session_store import get_session, save_session
from conversation.resolve import resolve_followup
from conversation.state import set_product, default_state
from generation.consumer_view import to_consumer_friendly
from routing.query_router import classify_query


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Same models api/main.py preloads — get_resources() caches globally,
    # so if that process already ran in this interpreter the second call
    # is free; each is a separate process in practice, so this pays the
    # load cost once per process, exactly like api/main.py does.
    get_resources()
    yield
    # Langfuse batches trace data on a background interval — flushing
    # explicitly on shutdown guarantees the last handful of requests'
    # traces are actually sent instead of being silently dropped when the
    # process exits (see ask_langchain_hybrid.py's own __main__ block for
    # the same fix on the CLI side). No-op if Langfuse was never
    # configured (get_client() with no credentials just has nothing to
    # flush).
    from ask_langchain_hybrid import _langfuse_handler
    if _langfuse_handler is not None:
        from langfuse import get_client
        get_client().flush()


app = FastAPI(title="Quick-Commerce RAG API (LangChain pipeline)", lifespan=lifespan)


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=1000)
    product_id: str | None = None
    session_id: str | None = None


class ChatResponse(BaseModel):
    answer: str
    answer_technical: str
    route: str
    product_id: str | None = None
    sources: list[Source] = []
    confidence: str = "medium"
    top_score: float | None = None
    injection_flagged: bool = False
    # LangChain-pipeline-specific observability, not present in
    # api/main.py's response — see module docstring.
    tool_trace: list[str] = []
    timing: dict[str, float] = {}
    usage: list[dict] = []


@app.get("/health")
def health():
    return {"status": "ok", "pipeline": "ask_langchain_hybrid"}


def _prep_request(req: ChatRequest, request: Request) -> tuple[dict, bool, object]:
    """
    Shared setup for both /api/chat and /api/chat/stream: rate limiting,
    injection flagging, session lookup, and syncing an explicit
    `product_id` into conversation state. Returns (state, injection_flagged,
    route) — `route` is only used to report `product_id`/whether this is
    the deterministic product_fact fast path, computed via the SAME
    classify_query() call ask()/ask_stream() make internally (a second
    call, not a second implementation — see api/main.py's own comment at
    this exact point for why req.query, not the here-resolved text, is
    what actually gets passed to ask()/ask_stream()).
    """
    client_id = request.client.host if request.client else "unknown"
    allowed, retry_after = check_rate_limit(client_id)
    if not allowed:
        raise HTTPException(
            status_code=429, detail=f"Rate limit exceeded — try again in {retry_after}s.",
            headers={"Retry-After": str(retry_after)},
        )

    injection_flagged = detect_prompt_injection(req.query)
    state = get_session(req.session_id) if req.session_id else default_state()

    conn = get_sqlite_conn()
    if req.product_id:
        row = conn.execute("SELECT name FROM products WHERE product_id = ?", (req.product_id,)).fetchone()
        if row is not None:
            set_product(state, req.product_id, row["name"])
    conn.close()

    resolved_query = resolve_followup(req.query, state)
    conn = get_sqlite_conn()
    route = classify_query(resolved_query, conn)
    conn.close()

    return state, injection_flagged, route


def _report_route(route, chunks: list[dict] | None, answer_technical: str) -> str:
    if route.route == "product_fact":
        return "product_fact"
    if chunks is None and answer_technical != INSUFFICIENT_EVIDENCE_MESSAGE:
        return "product_comparison"
    return "retrieval"


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest, request: Request):
    state, injection_flagged, route = _prep_request(req, request)

    resources = get_resources()
    timing: dict[str, float] = {}
    usage: list[dict] = []
    tool_trace: list[str] = []
    answer_technical, chunks = ask(
        req.query, verbose=False, resources=resources, conversation_state=state,
        return_chunks=True, timing=timing, usage=usage, tool_trace=tool_trace,
    )
    if req.session_id:
        save_session(req.session_id, state)

    reported_route = _report_route(route, chunks, answer_technical)
    sources = _build_sources(answer_technical, chunks)
    confidence, top_score = _confidence(reported_route, chunks)

    return ChatResponse(
        answer=to_consumer_friendly(answer_technical), answer_technical=answer_technical,
        route=reported_route, product_id=route.product_id or state.get("product_id"), sources=sources,
        confidence=confidence, top_score=top_score, injection_flagged=injection_flagged,
        tool_trace=tool_trace, timing={k: round(v, 4) for k, v in timing.items()}, usage=usage,
    )


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest, request: Request):
    """
    Server-Sent Events version of /api/chat, using ask_langchain_hybrid.py's
    ask_stream() — see that function's docstring for the streaming/
    groundedness tradeoff (raw tokens stream live for perceived speed; the
    final `event: final` payload carries the groundedness/consistency-
    checked authoritative text, since ⚠️ [UNVERIFIED...] markers can only
    be computed after the complete answer exists). A client should render
    `token` events live and swap in `final.answer` once it arrives.
    """
    state, injection_flagged, route = _prep_request(req, request)
    resources = get_resources()

    def event_stream():
        timing: dict[str, float] = {}
        usage: list[dict] = []
        tool_trace: list[str] = []
        for piece in ask_stream(
            req.query, verbose=False, resources=resources, conversation_state=state,
            timing=timing, usage=usage, tool_trace=tool_trace,
        ):
            if isinstance(piece, dict):
                answer_technical, chunks = piece["answer"], piece["chunks"]
                if req.session_id:
                    save_session(req.session_id, state)
                reported_route = _report_route(route, chunks, answer_technical)
                sources = _build_sources(answer_technical, chunks)
                confidence, top_score = _confidence(reported_route, chunks)
                final_payload = {
                    "answer": to_consumer_friendly(answer_technical), "answer_technical": answer_technical,
                    "route": reported_route, "product_id": route.product_id or state.get("product_id"),
                    "sources": [s.model_dump() for s in sources], "confidence": confidence,
                    "top_score": top_score, "injection_flagged": injection_flagged,
                    "tool_trace": tool_trace, "timing": {k: round(v, 4) for k, v in timing.items()}, "usage": usage,
                }
                yield f"event: final\ndata: {_json.dumps(final_payload)}\n\n"
            else:
                yield f"event: token\ndata: {_json.dumps({'text': piece})}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
