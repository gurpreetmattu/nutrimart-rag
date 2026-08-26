"""
ask_langchain_hybrid.py — LangChain-native pipeline with full behavioral
parity to ask_hybrid.py (Phase 5 hybrid + conversation layer). Sits
alongside ask.py, ask_hybrid.py, and ask_langchain.py (the naive LangChain
demo) — none of those files are touched by this one.

Scope: this ports EVERYTHING ask_hybrid.py does — BM25+dense fusion,
cross-encoder reranking, corrective retry/query rewriting, the
comparison_group override, groundedness checking, LLM tool-calling agent
routing, conversation state/follow-up resolution, the health-judgment and
composition-verdict regex safety-nets, and cross-turn consistency
checking — requested explicitly as "full parity," not the narrower 6-item
cut ask_langchain.py's naive version would have needed.

How this is actually "LangChain," honestly stated:
  - The two places an LLM makes a real DECISION are LangChain-native:
    tool-routing and final-answer generation, both issued through
    groq_gateway_invoke() below rather than gateway.complete_raw()/
    complete(). This is a LangChain-native reimplementation of
    generation/gateway.py's FULL behavior, not just the Groq-then-HF
    fallback: multi-key rotation (generation/gateway.py::_load_groq_api_keys,
    reused directly) and the proactive per-key daily token-budget ledger
    (generation/token_budget.py, reused directly — has_budget()/
    record_actual_usage() are the SAME ledger file gateway.py's own calls
    write to, so ask_hybrid.py and this pipeline share one real quota
    picture, not two independently-tracked ones) both apply here, then
    falls back to a HuggingFace ChatHuggingFace model (LangChain-native)
    only once every configured key is proactively judged over-budget or
    actually rate-limited — same three-layer shape gateway.py's
    complete_raw() has (proactive skip -> reactive RateLimitError catch ->
    HF fallback), reusing its own key list and budget ledger rather than
    re-deriving a second, divergent copy of either.
  - Every piece of business logic that ISN'T itself an LLM call — BM25
    fusion, RRF, cross-encoder reranking, the comparison_group tag match,
    doc_type/ingredient-entity scoping, structured SQL tool dispatch,
    conversation-state bookkeeping, follow-up resolution, the
    health-judgment/composition-verdict/compound-clause regex patterns,
    and consistency checking — is REUSED DIRECTLY from the existing,
    already-verified modules (retrieval/search_hybrid.py, agent/tools.py,
    conversation/state.py, conversation/resolve.py,
    generation/consistency.py, ask_hybrid.py's own module-level regex
    constants). Reimplementing correct, already-tested pure logic a
    second time in "LangChain style" would add risk (a second, divergent
    copy of hard-won bug fixes like Finding 16's comparison_group
    same-file false-positive fix) without adding anything LangChain
    actually contributes — LangChain has no abstraction for "cross-encoder
    rerank a fused RRF pool" or "does this query mention a health
    condition," these are just Python.
  - retrieve_hybrid_with_retry() itself (corrective retry + rewrite_query
    + comparison_group override) is imported directly from hybrid_core.py
    rather than rebuilt — it already accepts a `resources` dict for
    caller-supplied model/index instances, which is exactly what this
    file's LangChain retriever wrapper constructs. rewrite_query() (the
    corrective-retry query rewrite) also stays on generation/llm.py's
    existing gateway-backed implementation rather than being re-plumbed
    through ChatGroq — it has a specific, tested empty-string-fallback
    fix (see llm.py's docstring) that's tuned to this exact model's
    behavior; duplicating it via a second call path risks losing that fix
    silently.

Not a fork of ask_hybrid.py's file — a separate entrypoint that imports
and reuses hybrid_core.py's shared logic directly (retrieve_hybrid_with_retry,
its module-level regex constants, RERANK_SCORE_THRESHOLD,
INSUFFICIENT_EVIDENCE_MESSAGE — extracted from ask_hybrid.py 2026-08-26
specifically so this file doesn't need to depend on that one) rather than
copy-pasting them, so a future
fix to that shared logic doesn't silently diverge between the two
pipelines.
"""
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from dotenv import load_dotenv
load_dotenv()

from groq import RateLimitError as GroqRateLimitError, BadRequestError as GroqBadRequestError
from langchain_community.cache import SQLiteCache
from langchain_core.globals import set_llm_cache
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from sentence_transformers import SentenceTransformer

from config import EMBEDDING_MODEL, get_qdrant_client, get_sqlite_conn
from routing.query_router import classify_query, _COMPOUND_CLAUSE_RE, _HEALTH_CONDITION_RE
from structured.product_facts import (
    answer_product_fact, get_product_row, get_all_nutrition_facts, NUTRITION_LABELS,
)
from structured.product_ingredients import get_product_ins_codes
from retrieval.bm25_index import build_bm25_index
from retrieval.rerank import get_cross_encoder
from generation.llm import SYSTEM_PROMPT, build_context_block, build_known_facts_block
from generation.groundedness import check_groundedness
from generation.consistency import check_conversation_consistency
from generation.gateway import _load_groq_api_keys
from generation.token_budget import (
    DAILY_TOKEN_LIMIT, estimate_request_tokens, has_budget, record_actual_usage,
)
from conversation.resolve import resolve_followup
from conversation.state import record_fact, set_active_topic
from agent.tools import TOOL_SCHEMAS, STRUCTURED_TOOL_NAMES, dispatch_structured_tool, NO_PRODUCT_CONTEXT_MESSAGE
from timing import timed

# Reused directly from hybrid_core.py (not duplicated) — see that module's
# docstring on why duplicating these would be a real risk, not a style
# choice, and why this import no longer needs to reach into ask_hybrid.py
# itself (2026-08-26 — hybrid_core.py was extracted specifically so this
# pipeline doesn't depend on that hand-rolled-pipeline file).
from hybrid_core import (
    retrieve_hybrid_with_retry, _TOOL_TOPIC, _HEALTH_JUDGMENT_RE, _COMPOSITION_VERDICT_RE,
    _REGULATORY_LIMIT_RE, _CLAIM_ELIGIBILITY_RE, _DIETARY_CLASSIFICATION_RE,
    _NUTRITIONAL_VERDICT_RE, _fuzzy_verdict_trigger, _direct_ingredient_allergen_context,
    _build_agent_context_block, _sync_product_into_state,
    AGENT_SYSTEM_PROMPT_TEMPLATE, INSUFFICIENT_EVIDENCE_MESSAGE,
)

GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")
HF_MODEL = "Qwen/Qwen2.5-72B-Instruct"  # same fallback model gateway.py uses, see its docstring for why
GENERATION_REASONING_EFFORT = "low"  # same real-data-backed default as generation/llm.py

# Global exact-match response cache — a LangChain-native feature
# generation/gateway.py's hand-rolled call layer has no equivalent of.
# set_llm_cache() intercepts EVERY BaseChatModel.invoke()/.stream() call
# (ChatGroq and ChatHuggingFace both qualify) before it reaches the
# network: an identical (prompt, model, params) tuple returns the cached
# response with zero latency, zero token spend, and — because it never
# reaches _try_groq_all_keys() — zero budget-ledger impact, which is
# correct (a cache hit didn't really call Groq, so it shouldn't count
# against the daily quota tracked in token_budget_state.json). Persisted
# to a SQLite file (not the in-memory-only langchain_core.InMemoryCache)
# so it survives process restarts — genuinely useful for repeated eval
# runs and demo queries, though it's an EXACT-match cache (byte-identical
# prompt), so it won't help varied real user phrasing of "the same"
# question; that would need a semantic/embedding-based cache, a
# meaningfully bigger feature this project's KB (only ~120 chunks, cheap
# to just re-retrieve) doesn't obviously need yet. langchain_community's
# SQLiteCache is a deprecated-but-still-functional import as of the
# version this project pins (langchain_core's replacement is in-memory
# only) — noted here so it's not mistaken for an oversight if a future
# LangChain upgrade removes it; langchain_core.caches.InMemoryCache is the
# drop-in fallback if that happens.
set_llm_cache(SQLiteCache(database_path=str(Path(__file__).resolve().parent.parent / "langchain_cache.sqlite")))

# Langfuse tracing (used instead of LangSmith — same purpose, different
# backend: a visual trace of every retrieval/tool-call/generation step per
# query). Unlike LangSmith, Langfuse's LangChain integration is NOT
# purely env-var-driven auto-instrumentation — it's a real
# langchain_core.callbacks.BaseCallbackHandler that has to be attached to
# each model instance's `callbacks=[...]` at construction time. Every
# ChatGroq/ChatHuggingFace constructed anywhere in this file (see
# _try_groq_all_keys()/groq_gateway_stream()) is given this SAME handler
# instance, so a single query's tool-routing call, generation call, and
# any HF fallback call all land as one connected trace, not separate
# disconnected ones. Built lazily and only if LANGFUSE_PUBLIC_KEY is set
# (needs a free account at cloud.langfuse.com, or a self-hosted instance —
# not something this code can provision on its own); every construction
# site checks `_LANGFUSE_CALLBACKS`, which is `[]` (not `[handler]`) when
# no key is configured, so tracing is fully inert with zero behavior
# change until you add credentials.
_langfuse_handler = None
if os.environ.get("LANGFUSE_PUBLIC_KEY"):
    from langfuse.langchain import CallbackHandler as _LangfuseCallbackHandler
    _langfuse_handler = _LangfuseCallbackHandler()
_LANGFUSE_CALLBACKS = [_langfuse_handler] if _langfuse_handler is not None else []


_groq_key_index = 0  # mirrors gateway.py's own module-level cursor — remembers the last-good key


def _messages_to_plain(messages: list) -> list[dict]:
    """
    token_budget.py's estimator expects the plain {"role", "content"} shape
    gateway.py already builds by hand — converts LangChain message objects
    (or plain dicts, passed through unchanged) into that shape so the SAME
    estimator function applies here without a second implementation.
    """
    role_map = {"system": "system", "human": "user", "ai": "assistant"}
    out = []
    for m in messages:
        if isinstance(m, dict):
            out.append(m)
        else:
            content = m.content if isinstance(m.content, str) else str(m.content)
            out.append({"role": role_map.get(getattr(m, "type", ""), "user"), "content": content})
    return out


def _record_usage_lc(usage_out: list | None, call_name: str, provider: str, response: AIMessage) -> None:
    """
    Same entry shape as generation/gateway.py::_record_usage() (call,
    provider, prompt_tokens, completion_tokens, reasoning_tokens,
    total_tokens) — this consistent shape is what api/main_langchain.py's
    `usage` response field surfaces directly.
    """
    if usage_out is None:
        return
    usage = response.usage_metadata
    if not usage:
        return
    reasoning_tokens = (usage.get("output_token_details") or {}).get("reasoning", 0)
    usage_out.append({
        "call": call_name,
        "provider": provider,
        "prompt_tokens": usage.get("input_tokens", 0),
        "completion_tokens": usage.get("output_tokens", 0),
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": usage.get("total_tokens", 0),
    })


def _try_groq_all_keys(messages: list, max_tokens: int, tools: list | None, tool_choice: str | None) -> AIMessage | None:
    """
    One pass over every configured Groq key (proactive budget skip, then a
    real call). Returns the response on success, or None if every key was
    skipped/rate-limited (caller decides what to do next). A
    GroqBadRequestError from an attempted call propagates straight out —
    the caller (groq_gateway_invoke) owns the tool_use_failed retry/
    downgrade decision, mirroring gateway.py::_groq_create() /
    complete_raw()'s own split of responsibilities.
    """
    global _groq_key_index
    keys = _load_groq_api_keys()
    estimated_tokens = estimate_request_tokens(_messages_to_plain(messages), max_tokens)

    for offset in range(len(keys)):
        idx = (_groq_key_index + offset) % len(keys)
        if not has_budget(idx, estimated_tokens):
            print(f"[gateway_lc] Groq key #{idx + 1}/{len(keys)} skipped — proactive token-budget "
                  f"check predicts it's too close to its daily limit (~{estimated_tokens} est. tokens).")
            continue
        chat = ChatGroq(
            model=GROQ_MODEL, api_key=keys[idx], max_tokens=max_tokens,
            reasoning_effort=GENERATION_REASONING_EFFORT, callbacks=_LANGFUSE_CALLBACKS,
        )
        if tools is not None:
            chat = chat.bind_tools(tools, tool_choice=tool_choice)
        try:
            response = chat.invoke(messages)
            _groq_key_index = idx
            usage = response.usage_metadata
            if usage:
                record_actual_usage(idx, usage.get("total_tokens"))
            return response
        except GroqRateLimitError:
            record_actual_usage(idx, DAILY_TOKEN_LIMIT)
            print(f"[gateway_lc] Groq key #{idx + 1}/{len(keys)} rate-limited, trying next key...")
            continue
        # GroqBadRequestError (and anything else) propagates immediately —
        # not a per-key problem, so trying the next key wouldn't help.

    return None


def groq_gateway_invoke(
    messages: list, max_tokens: int, call_name: str = "call", tools: list | None = None,
    tool_choice: str | None = None, usage_out: list | None = None,
) -> AIMessage:
    """
    LangChain-native port of generation/gateway.py::complete_raw() — same
    layered shape: proactive per-key budget skip -> reactive
    GroqRateLimitError catch (next key) -> GroqBadRequestError
    "tool_use_failed" retry, then downgrade to tool_choice="auto" (a real,
    reproducible Groq constrained-decoding failure on subjective/
    evaluative questions — see ask_hybrid.py's comment at its tool-routing
    call site) -> HuggingFace fallback. Reuses gateway.py's own
    _load_groq_api_keys() and token_budget.py's ledger directly
    (has_budget()/record_actual_usage()) rather than a second, divergent
    copy of either — writes to and reads from the same
    token_budget_state.json file gateway.py's own calls use.

    `usage_out`, if given, gets an entry appended in the exact shape
    generation/gateway.py::_record_usage() uses (call/provider/
    prompt_tokens/completion_tokens/reasoning_tokens/total_tokens).

    Returns a real LangChain AIMessage in every case (Groq or HF), so
    callers use .content/.tool_calls exactly as with a plain ChatGroq call.
    """
    try:
        response = _try_groq_all_keys(messages, max_tokens, tools, tool_choice)
        if response is not None:
            _record_usage_lc(usage_out, call_name, "groq", response)
            return response
    except GroqBadRequestError as e:
        if tool_choice == "required" and "tool_use_failed" in str(e):
            print(f"[gateway_lc] Groq tool_choice=required failed ({call_name}): {e}\n"
                  f"[gateway_lc] Retrying with tool_choice=required again...")
            try:
                response = _try_groq_all_keys(messages, max_tokens, tools, tool_choice)
                if response is not None:
                    _record_usage_lc(usage_out, call_name, "groq", response)
                    return response
            except GroqBadRequestError as e2:
                if "tool_use_failed" not in str(e2):
                    raise
                print(f"[gateway_lc] Groq tool_choice=required failed again ({call_name}): {e2}\n"
                      f"[gateway_lc] Falling back to tool_choice=auto...")
                try:
                    response = _try_groq_all_keys(messages, max_tokens, tools, "auto")
                    if response is not None:
                        _record_usage_lc(usage_out, call_name, "groq", response)
                        return response
                except GroqBadRequestError:
                    pass  # falls through to the shared HF fallback below
        else:
            raise

    print(f"[gateway_lc] Falling back to Hugging Face ({HF_MODEL}) for {call_name} — "
          f"Groq keys exhausted/rate-limited or repeatedly failed tool_use_failed.")
    hf_endpoint = HuggingFaceEndpoint(
        repo_id=HF_MODEL, huggingfacehub_api_token=os.environ.get("HF_TOKEN"),
        max_new_tokens=max_tokens, task="conversational",
    )
    hf_chat = ChatHuggingFace(llm=hf_endpoint, callbacks=_LANGFUSE_CALLBACKS)
    if tools is not None:
        # HF's tool-calling doesn't support Groq's strict tool_choice=
        # "required" the same way — "auto" is the honest equivalent for a
        # fallback provider we don't have that same hardening for.
        #
        # Real bug found live 2026-08-26 (first time this fallback path
        # actually ran with multiple tools, once Groq's daily quota was
        # genuinely exhausted): the installed langchain_huggingface's
        # ChatHuggingFace.bind_tools() raises ValueError for ANY truthy
        # tool_choice — including "auto" — unless exactly one tool is
        # bound; this project's agent_tool_routing call always binds all 4
        # of TOOL_SCHEMAS, so "auto" was never actually valid here. Passing
        # None when there's more than one tool avoids the incompatibility
        # entirely (the model still sees every tool and decides freely,
        # the closest available behavior to "auto"); a genuine single-tool
        # call (none exist in this codebase today, but the guard costs
        # nothing) still gets the real tool_choice honored.
        hf_tool_choice = None
        if len(tools) == 1:
            hf_tool_choice = "auto" if tool_choice == "required" else tool_choice
        hf_chat = hf_chat.bind_tools(tools, tool_choice=hf_tool_choice)
    response = hf_chat.invoke(messages)
    _record_usage_lc(usage_out, call_name, "huggingface", response)
    return response


def build_resources() -> dict:
    dense_model = SentenceTransformer(EMBEDDING_MODEL)
    qdrant_client = get_qdrant_client()
    bm25_index, bm25_chunks = build_bm25_index(Path("data/raw"))
    cross_encoder = get_cross_encoder()
    return {
        "dense_model": dense_model, "qdrant_client": qdrant_client,
        "bm25_index": bm25_index, "bm25_chunks": bm25_chunks, "cross_encoder": cross_encoder,
    }


GENERATE_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    ("human", "{user_message}"),
])


def _build_generate_messages(query: str, chunks: list[dict], known_facts: dict | None,
                              structured_context: str | None) -> list:
    """Shared prompt-building for generate_answer_lc()/generate_answer_lc_stream()."""
    context_block = build_context_block(chunks) if chunks else ""

    known_facts_section = ""
    if known_facts:
        known_facts_section = (
            f"Known facts established earlier in this conversation:\n"
            f"{build_known_facts_block(known_facts)}\n\n---\n\n"
        )

    structured_section = ""
    if structured_context:
        structured_section = (
            f"Already answered this turn by a direct data lookup (ground truth — do not "
            f"contradict, hedge against, or re-derive a different answer for this):\n"
            f"{structured_context}\n\n---\n\n"
        )

    user_message = f"""{known_facts_section}{structured_section}Retrieved context:

{context_block}

---

User question: {query}"""

    return GENERATE_PROMPT.invoke({"user_message": user_message}).to_messages()


def generate_answer_lc(query: str, chunks: list[dict], known_facts: dict | None = None,
                        structured_context: str | None = None, usage_out: list | None = None) -> str:
    """
    LCEL-prompt-built replacement for generation/llm.py::generate_answer()
    — same SYSTEM_PROMPT/typed-claim contract and the same
    build_context_block()/build_known_facts_block() formatting (imported,
    not re-derived), issued through groq_gateway_invoke() (full key-
    rotation/budget/HF-fallback parity with gateway.complete()) instead of
    calling it directly. This is the "final generation" LangChain-native
    call point described in the module docstring.
    """
    messages = _build_generate_messages(query, chunks, known_facts, structured_context)
    response = groq_gateway_invoke(messages, max_tokens=2048, call_name="generate_answer", usage_out=usage_out)
    return response.content


def groq_gateway_stream(messages: list, max_tokens: int, call_name: str = "stream", usage_out: list | None = None):
    """
    Streaming counterpart to groq_gateway_invoke(), generation-only (no
    `tools` param — tool-calling needs the FULL response parsed before
    dispatch, so the tool-routing decision in ask() stays on the
    non-streaming groq_gateway_invoke()). Yields text chunks as they
    arrive via ChatGroq.stream(), instead of blocking for the whole
    response — the real latency win (~1.7s of blocking generation time
    measured earlier becomes visible token-by-token instead).

    Same proactive per-key budget check as groq_gateway_invoke(), but a
    narrower fallback contract, stated honestly: once real content has
    already been yielded to the caller for a given key, a mid-stream
    failure on THAT key propagates rather than silently switching
    providers — resuming on a different provider mid-stream would mean
    re-sending duplicate partial text to whatever is consuming this
    generator (an SSE client, e.g.), which is worse than a clean failure.
    Only falls back to Hugging Face when a key fails before yielding any
    content at all (i.e. every attempted key struck out before real
    output started), exactly mirroring groq_gateway_invoke()'s
    all-keys-exhausted case.
    """
    global _groq_key_index
    keys = _load_groq_api_keys()
    estimated_tokens = estimate_request_tokens(_messages_to_plain(messages), max_tokens)

    for offset in range(len(keys)):
        idx = (_groq_key_index + offset) % len(keys)
        if not has_budget(idx, estimated_tokens):
            print(f"[gateway_lc] Groq key #{idx + 1}/{len(keys)} skipped — proactive token-budget "
                  f"check predicts it's too close to its daily limit (~{estimated_tokens} est. tokens).")
            continue
        chat = ChatGroq(
            model=GROQ_MODEL, api_key=keys[idx], max_tokens=max_tokens,
            reasoning_effort=GENERATION_REASONING_EFFORT, callbacks=_LANGFUSE_CALLBACKS,
        )
        started = False
        total_tokens_seen = 0
        try:
            for chunk in chat.stream(messages):
                if chunk.content:
                    started = True
                    _groq_key_index = idx
                    yield chunk.content
                usage = getattr(chunk, "usage_metadata", None)
                if usage:
                    total_tokens_seen = usage.get("total_tokens") or total_tokens_seen
            if total_tokens_seen:
                record_actual_usage(idx, total_tokens_seen)
                if usage_out is not None:
                    usage_out.append({
                        "call": call_name, "provider": "groq", "prompt_tokens": None,
                        "completion_tokens": None, "reasoning_tokens": None, "total_tokens": total_tokens_seen,
                    })
            return
        except GroqRateLimitError:
            record_actual_usage(idx, DAILY_TOKEN_LIMIT)
            if started:
                print(f"[gateway_lc] Groq key #{idx + 1}/{len(keys)} rate-limited mid-stream "
                      f"({call_name}) — already yielded partial content, cannot cleanly fall back.")
                raise
            print(f"[gateway_lc] Groq key #{idx + 1}/{len(keys)} rate-limited, trying next key...")
            continue

    print(f"[gateway_lc] Falling back to Hugging Face ({HF_MODEL}) for {call_name}.")
    hf_endpoint = HuggingFaceEndpoint(
        repo_id=HF_MODEL, huggingfacehub_api_token=os.environ.get("HF_TOKEN"),
        max_new_tokens=max_tokens, task="conversational",
    )
    hf_chat = ChatHuggingFace(llm=hf_endpoint, callbacks=_LANGFUSE_CALLBACKS)
    for chunk in hf_chat.stream(messages):
        if chunk.content:
            yield chunk.content


def generate_answer_lc_stream(query: str, chunks: list[dict], known_facts: dict | None = None,
                               structured_context: str | None = None, usage_out: list | None = None):
    """Streaming counterpart to generate_answer_lc() — yields text chunks instead of returning a full string."""
    messages = _build_generate_messages(query, chunks, known_facts, structured_context)
    yield from groq_gateway_stream(messages, max_tokens=2048, call_name="generate_answer", usage_out=usage_out)


class _RouteResult:
    """
    Everything ask()/ask_stream() need after routing/tool-dispatch/
    retrieval decide what to do, but before the final generation call —
    factored out specifically so streaming and non-streaming callers share
    ONE copy of the routing/retrieval control flow (agent tool-calling
    decision, structured-tool dispatch, the two safety-net retries, the
    composition-verdict/structured-only/insufficient-evidence early-outs)
    instead of a second, divergent copy for the streaming path.

    `done=True` means `answer` (and `chunks`, possibly None) is already
    the final result — nothing left to generate (product_fact route,
    structured-tools-only, or insufficient-evidence). `done=False` means
    the caller still needs to call generate_answer_lc()/
    generate_answer_lc_stream() with `resolved_query`/`chunks`/
    `known_facts`/`structured_context`; `verdict_mode=True` marks the
    composition-verdict case, where groundedness checking is skipped
    (there are no retrieved chunks to check claims against — see
    ask_hybrid.py's own comment at this exact branch) and the caller
    should report `chunks=None`, not `[]`, in any return_chunks tuple.
    """

    def __init__(self, done: bool, answer: str | None = None, chunks: list[dict] | None = None,
                 resolved_query: str | None = None, known_facts: dict | None = None,
                 structured_context: str | None = None, structured_answers: list[str] | None = None,
                 verdict_mode: bool = False):
        self.done = done
        self.answer = answer
        self.chunks = chunks
        self.resolved_query = resolved_query
        self.known_facts = known_facts
        self.structured_context = structured_context
        self.structured_answers = structured_answers or []
        self.verdict_mode = verdict_mode


def _route_and_retrieve(
    query: str, top_k: int, verbose: bool, resources: dict, conversation_state: dict | None,
    timing: dict | None, usage: list | None, tool_trace: list | None,
) -> _RouteResult:
    """
    Routing -> agent tool-call decision -> structured dispatch / hybrid
    retrieval, i.e. everything in ask_hybrid.py::ask_hybrid() before its
    final generate_answer() call. See _RouteResult's docstring for why
    this is split out. Owns opening/closing the sqlite connection for its
    own lifetime — callers never see it.
    """
    resolved_query = resolve_followup(query, conversation_state) if conversation_state is not None else query

    sqlite_conn = get_sqlite_conn()
    route = classify_query(resolved_query, sqlite_conn)
    if conversation_state is not None:
        _sync_product_into_state(conversation_state, route.product_id, sqlite_conn)

    effective_product_id = route.product_id
    if effective_product_id is None and conversation_state is not None:
        effective_product_id = conversation_state.get("product_id")

    if route.route == "product_fact":
        if verbose:
            print(f"\nRouted to product_fact ({route.product_id}, field={route.fact_field})\n")
        answer = answer_product_fact(route.product_id, route.fact_field, sqlite_conn)
        if tool_trace is not None:
            tool_trace.append("product_fact")
        if conversation_state is not None:
            set_active_topic(conversation_state, "nutrition" if route.fact_field in NUTRITION_LABELS else "product_fact")
            if route.fact_field in NUTRITION_LABELS:
                row = get_product_row(route.product_id, sqlite_conn)
                if row is not None:
                    value = json.loads(row["nutrition_json"] or "{}").get("values", {}).get(route.fact_field)
                    if value is not None:
                        label, unit = NUTRITION_LABELS[route.fact_field]
                        record_fact(conversation_state, route.fact_field, value, unit, "products.sqlite")
        sqlite_conn.close()
        return _RouteResult(done=True, answer=answer, chunks=None)

    # --- LangChain-native tool-calling decision round ---
    context_block = _build_agent_context_block(effective_product_id, sqlite_conn, conversation_state)
    agent_system_prompt = AGENT_SYSTEM_PROMPT_TEMPLATE.format(context_block=context_block)

    with timed(timing, "tool_routing"):
        decision = groq_gateway_invoke(
            [SystemMessage(content=agent_system_prompt), HumanMessage(content=resolved_query)],
            max_tokens=300, call_name="agent_tool_routing", tools=TOOL_SCHEMAS, tool_choice="required",
            usage_out=usage,
        )
    tool_calls = decision.tool_calls or []

    if not tool_calls:
        # Same last-resort fallback ask_hybrid.py uses when tool_choice=
        # "required" still declines (a real, reproducible Groq behavior on
        # subjective/evaluative questions under constrained decoding — see
        # ask_hybrid.py's comment at this exact point).
        product_ins_codes = get_product_ins_codes(effective_product_id, sqlite_conn) if effective_product_id else None
        chunks = retrieve_hybrid_with_retry(
            resolved_query, product_ins_codes=product_ins_codes, top_k=top_k,
            verbose=verbose, resources=resources, timing=timing, usage=usage,
        )
        if chunks is None:
            sqlite_conn.close()
            return _RouteResult(done=True, answer=INSUFFICIENT_EVIDENCE_MESSAGE, chunks=None)
        tool_names_fired = ["search_knowledge_base"]
    else:
        chunks = None
        tool_names_fired = [tc["name"] for tc in tool_calls]
    if tool_trace is not None:
        tool_trace.extend(tool_names_fired)

    structured_answers = []
    nutrition_fact_answers = []

    for tc in tool_calls:
        name = tc["name"]
        args = tc.get("args") or {}

        if name == "search_knowledge_base":
            # Always retrieve with the real resolved_query, never a
            # model-rewritten one (the tool no longer even exposes a
            # `query` argument, see agent/tools.py's comment on why —
            # 2026-08-24, this exact substitution silently broke q07's
            # comparison_group rescue).
            product_ins_codes = get_product_ins_codes(effective_product_id, sqlite_conn) if effective_product_id else None
            chunks = retrieve_hybrid_with_retry(
                resolved_query, product_ins_codes=product_ins_codes,
                top_k=top_k, verbose=verbose, resources=resources, timing=timing, usage=usage,
            )
        elif name in STRUCTURED_TOOL_NAMES:
            result = dispatch_structured_tool(name, args, effective_product_id, sqlite_conn)
            is_nutrition_fact = name == "lookup_product_fact" and args.get("field") in NUTRITION_LABELS
            if is_nutrition_fact:
                nutrition_fact_answers.append(result)
            else:
                structured_answers.append(result)
            if name == "lookup_product_fact" and effective_product_id and conversation_state is not None:
                field = args.get("field")
                if field in NUTRITION_LABELS:
                    row = get_product_row(effective_product_id, sqlite_conn)
                    if row is not None:
                        value = json.loads(row["nutrition_json"] or "{}").get("values", {}).get(field)
                        if value is not None:
                            label, unit = NUTRITION_LABELS[field]
                            record_fact(conversation_state, field, value, unit, "products.sqlite")
            elif name == "check_ingredient_or_allergen" and effective_product_id and conversation_state is not None:
                qty_m = re.search(r"label states\s+([\d.]+)\s*(mg|g|mcg|%|ppm)", result, re.IGNORECASE)
                ing_name = (args.get("name") or "").strip().lower()
                if qty_m and ing_name:
                    record_fact(
                        conversation_state, ing_name, float(qty_m.group(1)),
                        qty_m.group(2).lower(), "products.sqlite",
                    )

    if (chunks is None and (structured_answers or nutrition_fact_answers)
            and all(a == NO_PRODUCT_CONTEXT_MESSAGE for a in structured_answers + nutrition_fact_answers)
            and "search_knowledge_base" not in tool_names_fired):
        structured_answers = []
        nutrition_fact_answers = []
        chunks = retrieve_hybrid_with_retry(
            resolved_query, product_ins_codes=None, top_k=top_k, verbose=verbose,
            resources=resources, timing=timing, usage=usage,
        )

    if (chunks is None and "search_knowledge_base" not in tool_names_fired
            and (_HEALTH_JUDGMENT_RE.search(resolved_query) or _COMPOUND_CLAUSE_RE.search(resolved_query)
                 or _HEALTH_CONDITION_RE.search(resolved_query) or _REGULATORY_LIMIT_RE.search(resolved_query)
                 or _CLAIM_ELIGIBILITY_RE.search(resolved_query))):
        product_ins_codes = get_product_ins_codes(effective_product_id, sqlite_conn) if effective_product_id else None
        health_chunks = retrieve_hybrid_with_retry(
            resolved_query, product_ins_codes=product_ins_codes, top_k=top_k,
            verbose=verbose, resources=resources, timing=timing, usage=usage,
        )
        if health_chunks is not None:
            chunks = health_chunks
            tool_names_fired.append("search_knowledge_base")
            if tool_trace is not None:
                tool_trace.append("search_knowledge_base")

    if conversation_state is not None:
        fired_topic = next((_TOOL_TOPIC[n] for n in tool_names_fired if n in _TOOL_TOPIC), None)
        if fired_topic:
            set_active_topic(conversation_state, fired_topic)

    # See ask_hybrid.py's matching branch (Finding 40, 2026-08-26) for the
    # full reasoning on why the extended dietary/nutritional-verdict set
    # drops the `chunks is None` requirement and directly fetches real
    # ingredient/allergen data instead of trusting whichever tool fired.
    _extended_verdict_match = (
        _DIETARY_CLASSIFICATION_RE.search(resolved_query) or _NUTRITIONAL_VERDICT_RE.search(resolved_query)
        or _fuzzy_verdict_trigger(resolved_query)
    )
    if _extended_verdict_match and effective_product_id:
        direct_context = _direct_ingredient_allergen_context(effective_product_id, sqlite_conn)
        if direct_context and direct_context not in structured_answers:
            structured_answers = structured_answers + [direct_context]

    if ((structured_answers or nutrition_fact_answers)
            and (_extended_verdict_match or (chunks is None and _COMPOSITION_VERDICT_RE.search(resolved_query)))):
        structured_context = "\n\n".join(structured_answers + nutrition_fact_answers)
        verdict_known_facts = conversation_state.get("known_facts") if conversation_state is not None else None
        sqlite_conn.close()
        return _RouteResult(
            done=False, resolved_query=resolved_query, chunks=[], known_facts=verdict_known_facts,
            structured_context=structured_context, verdict_mode=True,
        )

    if chunks is None and (structured_answers or nutrition_fact_answers):
        answer = "\n\n".join(structured_answers + nutrition_fact_answers)
        sqlite_conn.close()
        return _RouteResult(done=True, answer=answer, chunks=None)

    if chunks is None:
        sqlite_conn.close()
        return _RouteResult(done=True, answer=INSUFFICIENT_EVIDENCE_MESSAGE, chunks=None)

    if verbose:
        print(f"\nRetrieved {len(chunks)} chunks:")
        for c in chunks:
            print(f"  - [rerank={c['rerank_score']:.3f}] {c['source_file']} — {c['heading']}")
        print()

    if effective_product_id:
        product_nutrition_facts = get_all_nutrition_facts(effective_product_id, sqlite_conn)
        if conversation_state is not None:
            for field, fact in product_nutrition_facts.items():
                conversation_state["known_facts"].setdefault(field, fact)
            known_facts = conversation_state["known_facts"]
        else:
            known_facts = product_nutrition_facts
    else:
        known_facts = conversation_state.get("known_facts") if conversation_state is not None else None

    sqlite_conn.close()

    structured_context = "\n\n".join(structured_answers) if structured_answers else None
    return _RouteResult(
        done=False, resolved_query=resolved_query, chunks=chunks, known_facts=known_facts,
        structured_context=structured_context, structured_answers=structured_answers,
    )


def ask(
    query: str, top_k: int = 5, verbose: bool = True, resources: dict | None = None,
    conversation_state: dict | None = None, return_chunks: bool = False,
    timing: dict | None = None, usage: list | None = None, tool_trace: list | None = None,
    return_structured_answers: bool = False, return_known_facts: bool = False,
) -> str | tuple:
    """
    Full-parity LangChain port of ask_hybrid.py::ask_hybrid() (a hand-rolled
    sibling pipeline this repo doesn't include, see ARCHITECTURE.md) — same
    control flow (routing -> agent tool-call decision -> structured
    dispatch / hybrid retrieval -> generation -> groundedness ->
    consistency), same conversation-state contract, same safety-net regex
    patterns. `return_chunks`/`timing`/`usage`/`tool_trace` are the
    observability params api/main.py and api/main_langchain.py actually use
    here; all default to no-op values, so plain `ask(query)` behaves
    identically without them. Routing/retrieval is shared with ask_stream()
    below via _route_and_retrieve() — this function only owns the
    blocking generate_answer_lc() call and groundedness/consistency
    checking. See the module docstring for exactly which pieces are
    LangChain-native calls vs. reused business logic.

    `return_structured_answers` (added 2026-08-25, for eval/ragas_metrics.py):
    when True, also returns the raw list of structured-tool answer strings
    (products.sqlite-grounded, e.g. from lookup_product_fact/
    check_ingredient_or_allergen) that got prepended to the final answer
    text, if any fired this turn. Needed because `check_groundedness()`
    (and this eval's own faithfulness/context-recall checks) only verify
    claims against the retrieved KB `chunks` — a structured tool's own
    output is separately, deterministically grounded in SQL and was never
    meant to be re-verified against KB context, but a caller checking the
    FULL final answer text (structured prefix + generated portion) against
    ONLY the KB chunks has no way to tell the two apart and will wrongly
    flag the SQL-grounded part as unsupported. Independent of
    `return_chunks` — combine both flags for a 3-tuple, either alone for a
    2-tuple, neither for the bare string (unchanged default).

    `return_known_facts` (added 2026-08-25, for eval/ragas_metrics.py's
    faithfulness() fix): also returns the same known_facts dict
    generate_answer_lc() used this turn (products.sqlite nutrition/
    ingredient data merged into the prompt) — needed because the generator
    legitimately weaves known_facts claims inline into the KB-grounded
    answer (not just via a structured-tool prefix), and a faithfulness
    check that only sees KB chunks as context wrongly flags those as
    unsupported. Independent of the other two return_* flags — appended as
    the last tuple element, in `return_chunks, return_structured_answers,
    return_known_facts` order, only for whichever flags are True.
    """
    _start = time.perf_counter()
    resources = resources or build_resources()

    def _shape(final_answer: str, chunks_out, structured_answers_out: list[str], known_facts_out: dict | None):
        extras = []
        if return_chunks:
            extras.append(chunks_out)
        if return_structured_answers:
            extras.append(structured_answers_out)
        if return_known_facts:
            extras.append(known_facts_out)
        return (final_answer, *extras) if extras else final_answer

    result = _route_and_retrieve(query, top_k, verbose, resources, conversation_state, timing, usage, tool_trace)
    if result.done:
        if timing is not None:
            timing["total"] = time.perf_counter() - _start
        return _shape(result.answer, result.chunks, [], None)

    with timed(timing, "generation"):
        answer = generate_answer_lc(
            result.resolved_query, result.chunks, known_facts=result.known_facts,
            structured_context=result.structured_context, usage_out=usage,
        )

    if not result.verdict_mode:
        with timed(timing, "groundedness_check"):
            answer = check_groundedness(answer, result.chunks)
        if result.structured_answers:
            answer = "\n\n".join(result.structured_answers) + "\n\n" + answer

    if conversation_state is not None:
        answer = check_conversation_consistency(answer, conversation_state)

    if timing is not None:
        timing["total"] = time.perf_counter() - _start
    reported_chunks = None if result.verdict_mode else result.chunks
    return _shape(answer, reported_chunks, result.structured_answers, result.known_facts)


def ask_stream(
    query: str, top_k: int = 5, verbose: bool = False, resources: dict | None = None,
    conversation_state: dict | None = None, timing: dict | None = None,
    usage: list | None = None, tool_trace: list | None = None,
):
    """
    Streaming counterpart to ask() — same routing/retrieval via the shared
    _route_and_retrieve(), but yields the final generation's text
    token-by-token (via generate_answer_lc_stream()) instead of blocking
    for the whole answer, then a final `{"final": True, "answer": ...,
    "chunks": ...}` dict once groundedness/consistency checking has run on
    the fully-assembled text.

    Stated honestly: groundedness's ⚠️ [UNVERIFIED...] markers can only be
    computed after the complete answer exists (check_groundedness() needs
    the whole claim to match against a cited chunk), so they're NEVER
    present in the streamed text chunks themselves — only in the final
    payload. A caller (e.g. an SSE endpoint) should stream the raw tokens
    for perceived speed, then swap in the final payload's `answer` as the
    authoritative version once it arrives, exactly the pattern real
    streaming+guardrail systems use.

    For the "already-final" cases (product_fact / structured-tools-only /
    insufficient-evidence) there's nothing to meaningfully stream — yields
    the whole answer as a single chunk, then the same final payload shape.
    """
    _start = time.perf_counter()
    resources = resources or build_resources()

    result = _route_and_retrieve(query, top_k, verbose, resources, conversation_state, timing, usage, tool_trace)

    if result.done:
        yield result.answer
        if timing is not None:
            timing["total"] = time.perf_counter() - _start
        yield {"final": True, "answer": result.answer, "chunks": result.chunks}
        return

    full_text = ""
    with timed(timing, "generation"):
        for piece in generate_answer_lc_stream(
            result.resolved_query, result.chunks, known_facts=result.known_facts,
            structured_context=result.structured_context, usage_out=usage,
        ):
            full_text += piece
            yield piece

    answer = full_text
    if not result.verdict_mode:
        with timed(timing, "groundedness_check"):
            answer = check_groundedness(answer, result.chunks)
        if result.structured_answers:
            answer = "\n\n".join(result.structured_answers) + "\n\n" + answer

    if conversation_state is not None:
        answer = check_conversation_consistency(answer, conversation_state)

    if timing is not None:
        timing["total"] = time.perf_counter() - _start
    reported_chunks = None if result.verdict_mode else result.chunks
    yield {"final": True, "answer": answer, "chunks": reported_chunks}


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "is aspartame safe in Diet Coke"

    print(f"Query: {query}\n{'='*60}")
    print("Loading models/index...")
    resources = build_resources()
    answer = ask(query, resources=resources)
    print(f"Answer:\n{'-'*60}")
    print(answer)

    if _langfuse_handler is not None:
        # Langfuse batches trace data and exports it on a background
        # interval — a short-lived CLI process can exit before that
        # interval fires, silently dropping the trace this exact run just
        # generated. Flushing explicitly on exit (only when Langfuse is
        # actually configured) guarantees the trace is sent, matching what
        # a long-lived server process's own shutdown hook does (see
        # api/main_langchain.py's lifespan).
        from langfuse import get_client
        get_client().flush()
