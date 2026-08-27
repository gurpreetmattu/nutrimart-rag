"""
hybrid_core.py — the hybrid-retrieval decision logic used by
ask_langchain_hybrid.py: corrective retry, the BM25-consensus check, the
comparison_group override, and the regex safety-nets (_HEALTH_JUDGMENT_RE
etc.) that force a knowledge-base search for evaluative/regulatory
questions.

Kept in its own module, separate from the LangChain entrypoint itself, so
this retrieval-decision logic exists in exactly one place rather than
being duplicated inline inside a LangChain-specific file — it's plain
Python either way, not something a LangChain abstraction models naturally
(see ARCHITECTURE.md §7).

What stays OUT of this file: the actual LLM call layer. That lives in
`ask_langchain_hybrid.py`'s own `groq_gateway_invoke()`, a LangChain-native
multi-key-rotation + proactive-budget + HF-fallback implementation
(`ChatGroq`/`ChatHuggingFace`) — this module only decides *what* to
retrieve, never how a model gets called.
"""
import difflib
import json
import re
from pathlib import Path

from sentence_transformers import SentenceTransformer

from config import get_qdrant_client, EMBEDDING_MODEL
from structured.product_facts import get_product_row
from retrieval.bm25_index import build_bm25_index
from retrieval.rerank import get_cross_encoder, rerank
from retrieval.search_hybrid import search_hybrid, find_comparison_group_match
from generation.llm import rewrite_query
from conversation.state import set_product
from timing import timed

# --- Tool-routing topic map: a single-round LLM tool-calling decision
# dispatches between structured lookups and knowledge-base retrieval ---
_TOOL_TOPIC = {
    "lookup_product_fact": "product_fact", "check_ingredient_or_allergen": "ingredient",
    "compare_products": "comparison", "search_knowledge_base": "regulatory",
}

# Safety net for evaluative/health-judgment questions ("is this healthy?",
# "is this good for kids?", "should I buy this?") — widened repeatedly
# against real query phrasings (a closed, stable vocabulary problem, not a
# whack-a-mole one).
_HEALTH_JUDGMENT_RE = re.compile(
    r"\bhealth(?:y|ier|iest)?\b|\bgood for\b|\bbad for\b|\bsafe for\b|\bsuitable for\b"
    r"|\bshould i (?:buy|eat|choose|pick|get)\b|\brecommend\b"
    r"|\bfor (?:kids|children|toddlers|babies)\b|\bweight loss\b|\bdiet(?:ing)?\b"
    r"|\btoo much\b|\btoo high\b|\btoo low\b|\ba lot\b"
    r"|\bnutritious\b|\b(?:ok|okay|fine|safe)\s+to\s+(?:eat|have|consume)\b"
    r"|\b(?:eat|consume|have)\b(?:\s+\S+){0,6}?\s+daily\b",
    re.IGNORECASE,
)

# Composition-verdict questions ("is this PURELY wheat?", "is it MOSTLY
# sugar?", "is this JUST X?") — verified against real test cases.
_COMPOSITION_VERDICT_RE = re.compile(
    r"\bpurely\b|\bentirely\b|\bexclusively\b|\bsolely\b|\bnothing but\b"
    r"|\bonly\b.{0,20}\b(?:made|wheat|sugar|milk|oil|flour|rice|corn|ingredient)\b"
    r"|\bjust\b.{0,20}\b(?:made|wheat|sugar|milk|oil|flour|rice|corn|water)\b"
    r"|\bbasically\b.{0,20}\ball\b|\bmostly\b|\bprimarily\b",
    re.IGNORECASE,
)

# Regulatory-limit questions ("what is the permitted/legal limit/level/
# amount/quantity of X") — see Finding 31 (2026-08-25, q21-q24).
_REGULATORY_LIMIT_RE = re.compile(
    r"\b(?:permitted|legal|regulatory|allowed|maximum|max)\s+(?:limit|level|amount|quantity)\b"
    r"|\bwithin\s+(?:the\s+|its\s+)?(?:legal\s+|permitted\s+|regulatory\s+)?limit\b",
    re.IGNORECASE,
)

# Claim-eligibility questions ("can it claim...", "is this a good source of
# protein") — see Findings 31/40 (2026-08-25/26, q27 and the broadened
# nutrient-claim vocabulary).
_CLAIM_ELIGIBILITY_RE = re.compile(
    r"\bclaim(?:s)?\b"
    r"|\b(?:good|rich|high|excellent|great)\s+(?:source\s+of|in)\b|\blow\s+in\b",
    re.IGNORECASE,
)

# Nutritional/compositional verdict questions ("is this nut-free/soy-free",
# "is this keto-friendly/low-carb", "is this junk food", "is this fortified",
# "is this whole grain") — see Finding 40 (2026-08-26).
_NUTRITIONAL_VERDICT_RE = re.compile(
    r"\b\w+[- ]free\b"  # nut-free, soy-free, egg-free, peanut-free, fat-free, caffeine-free, ...
    r"|\bketo(?:genic)?\b|\blow[- ]carb\b|\blow[- ]fat\b|\bhigh[- ]protein\b|\bpaleo\b|\bwhole30\b"
    r"|\bjunk\s+food\b|\bultra[- ]?processed\b"
    r"|\bfortified\b|\bfortification\b"
    r"|\bwhole\s+grain\b|\bwhole\s+wheat\b|\brefined\s+grain\b|\bmultigrain\b",
    re.IGNORECASE,
)

# Fuzzy typo-tolerance for the verdict-trigger vocabulary above (Finding 40).
# halal/kosher deliberately excluded — see Finding 40's comment: those
# genuinely benefit from real KB-chunk nuance and already produce a good,
# honestly-hedged answer via the normal flow.
_VERDICT_TRIGGER_WORDS = [
    "vegan", "vegans", "vegetarian", "vegetarians",
    "keto", "ketogenic", "paleo", "fortified", "organic",
]


def _fuzzy_verdict_trigger(query: str) -> bool:
    for token in re.findall(r"[a-zA-Z]+", query.lower()):
        if len(token) >= 4 and difflib.get_close_matches(token, _VERDICT_TRIGGER_WORDS, n=1, cutoff=0.8):
            return True
    return False


def _direct_ingredient_allergen_context(product_id: str, conn) -> str | None:
    """
    Directly fetches a product's real ingredients/allergens via
    get_product_row(), bypassing whatever check_ingredient_or_allergen's own
    fuzzy `name`-guess did or didn't find — see Finding 40's docstring for
    why this exists (guarantees real data reaches the verdict-synthesis
    branch independent of tool-selection variance).
    """
    row = get_product_row(product_id, conn)
    if row is None:
        return None
    contains = json.loads(row["allergens_contains_json"] or "[]")
    may_contain = json.loads(row["allergens_may_contain_json"] or "[]")
    allergen_text = f"Contains {', '.join(contains)}" if contains else "No declared allergens"
    if may_contain:
        allergen_text += f"; May Contain {', '.join(may_contain)}"
    return f"{row['name']}'s declared ingredients: {row['ingredients_raw']}. Allergen Information: {allergen_text}."


# Dietary-classification verdict questions ("is this vegan", "is this
# vegetarian", "is this dairy-free/gluten-free", "suitable for vegans") —
# see Finding 40's 2026-08-26 writeup (the vegan bug).
_DIETARY_CLASSIFICATION_RE = re.compile(
    r"\bvegans?\b|\bvegetarians?\b|\bplant[- ]based\b|\bdairy[- ]free\b|\bgluten[- ]free\b"
    r"|\bcontains?\s+animal\b|\banimal[- ]derived\b|\banimal\s+products?\b",
    re.IGNORECASE,
)

AGENT_SYSTEM_PROMPT_TEMPLATE = """You are a routing assistant for a quick-commerce grocery app's \
product chatbot. Your ONLY job this turn is to decide which tool(s) to call to answer the user's \
question — you do not write the final answer yourself when a tool's own output is already a \
complete, cited answer.

You MUST call at least one tool for any question about a product's facts, nutrition, ingredients, \
allergens, comparisons, alternatives, rankings, regulatory status, or health/safety — never answer \
from your own knowledge, even if you're confident you know the answer. If a question needs both the \
product's own data AND general regulatory/nutrition context (e.g. "is this healthy", "is this \
ingredient safe", "why does this need a preservative"), call the relevant structured tool(s) AND \
search_knowledge_base together in the same turn — don't guess which one is enough.

If "No product is currently in context" above, NEVER call lookup_product_fact or \
check_ingredient_or_allergen — they can only answer for a specific product and will fail. Use \
search_knowledge_base instead for any general regulatory/nutrition/ingredient question, even one \
phrased as if about "this product" or a named-but-unresolved product.

A question that asks whether to pick one ALREADY-NAMED variant/product over another (e.g. "should \
I pick the diet version instead of regular", "is X better than Y") is a regulatory/nutrition \
judgment call, not a request to find other database options — call search_knowledge_base for \
that, not compare_products (compare_products is for "what ELSE is available" questions that don't \
already name the alternative).

check_ingredient_or_allergen is ONLY for "is X declared IN this product" questions — a question \
merely MENTIONING a food word is NOT automatically an ingredient check. "Can I have this with milk", \
"what goes well with this", "how should I eat this" are serving/pairing questions, not asking \
whether milk is an ingredient — use search_knowledge_base for those instead (a genuine \
"insufficient evidence" result is the correct, honest answer if the KB doesn't cover serving \
suggestions; do NOT substitute an unrelated ingredient/allergen answer just because a tool must be \
called).

A question asking about a PERMITTED/LEGAL/REGULATORY LIMIT, LEVEL, or whether something is "within \
limits" ALWAYS needs search_knowledge_base, even if the ingredient/additive is already confirmed \
present via lookup_product_fact or check_ingredient_or_allergen — confirming an additive is IN a \
product never answers what its permitted limit IS, or whether the product's level complies with it. \
Call both together: the structured tool to confirm presence/quantity, search_knowledge_base for the \
actual regulatory limit. Do not treat "yes, it's a declared ingredient" as a complete answer to a \
limit/legal/permitted-level question.

{context_block}"""


def _build_agent_context_block(effective_product_id: str | None, sqlite_conn, conversation_state: dict | None) -> str:
    lines = []
    if effective_product_id:
        row = get_product_row(effective_product_id, sqlite_conn)
        if row is not None:
            lines.append(f"Current product in context: {row['name']} (product_id={effective_product_id}).")
    else:
        lines.append("No product is currently in context.")

    known_facts = (conversation_state or {}).get("known_facts") or {}
    if known_facts:
        facts_str = "; ".join(f"{k}={v['value']}{v['unit']}" for k, v in known_facts.items())
        lines.append(f"Facts already established earlier in this conversation: {facts_str}.")

    return "\n".join(lines)


# Sigmoid-space cross-encoder score threshold below which the corrective
# retry kicks in — validated against real observed score distributions,
# not guessed.
RERANK_SCORE_THRESHOLD = 0.3

INSUFFICIENT_EVIDENCE_MESSAGE = (
    "[UNCERTAIN] Insufficient evidence retrieved to answer this question "
    "confidently, even after a query rewrite retry."
)

# BM25-consensus skip for the corrective retry — see Finding 34 (2026-08-25,
# the q27 fix) for the full reasoning: a landslide raw-BM25 margin on the
# cross-encoder's own #1 pick is trustworthy evidence that pick is right,
# even when the cross-encoder's own absolute score can't be trusted alone.
BM25_CONSENSUS_RATIO = 1.4
BM25_CONSENSUS_MIN_SCORE = 5.0


def _has_bm25_consensus(full_pool: list[dict], top_chunk_id: str) -> bool:
    """
    True when `top_chunk_id` (the cross-encoder's own #1 pick) is ALSO a
    landslide winner by raw BM25 score within `full_pool`.
    """
    if not full_pool:
        return False
    bm25_sorted = sorted(full_pool, key=lambda c: c.get("bm25_score", 0.0), reverse=True)
    top = bm25_sorted[0]
    if top["bm25_score"] < BM25_CONSENSUS_MIN_SCORE or top["chunk_id"] != top_chunk_id:
        return False
    second_score = bm25_sorted[1]["bm25_score"] if len(bm25_sorted) > 1 else 0.0
    if second_score <= 0:
        return True
    return top["bm25_score"] / second_score >= BM25_CONSENSUS_RATIO


# Corroborated-chunk trim for context_precision — see Finding 35 (2026-08-25)
# for the full reasoning and the 5 real queries this was verified against
# before shipping.
CORROBORATION_ABS_FLOOR = 0.5


def _trim_to_corroborated_chunks(chunks: list[dict]) -> list[dict]:
    """
    `chunks` must already be sorted descending by rerank_score (rerank()'s
    own contract) — cross-encoder rank is just each chunk's list position.
    """
    if len(chunks) <= 2:
        return chunks
    by_bm25_rank = {
        c["chunk_id"]: i for i, c in enumerate(
            sorted(chunks, key=lambda c: c.get("bm25_score", 0.0), reverse=True)
        )
    }
    return [
        c for i, c in enumerate(chunks)
        if c["rerank_score"] >= CORROBORATION_ABS_FLOOR or i < 2 or by_bm25_rank[c["chunk_id"]] < 2
    ]


def retrieve_hybrid_with_retry(
    query: str, product_ins_codes: set[str] | None = None, top_k: int = 5, verbose: bool = True,
    resources: dict | None = None, timing: dict | None = None, usage: list | None = None,
    intent: str | None = None,
) -> list[dict] | None:
    """
    Runs search_hybrid, and if the top reranked score is below
    RERANK_SCORE_THRESHOLD, rewrites the query and retries once — UNLESS
    the top pick already shows a landslide BM25 consensus (see
    _has_bm25_consensus, Finding 34), in which case the retry is skipped
    and the original top-1 result is trusted despite its low absolute
    cross-encoder score. Returns None (meaning "insufficient evidence") if
    neither the BM25-consensus check nor the retry produces a confident
    result.

    `resources`, if given, must be a dict with dense_model/qdrant_client/
    bm25_index/bm25_chunks/cross_encoder already built — lets a long-lived
    caller (api/main.py, api/main_langchain.py) load these once at process
    startup instead of per-call. Defaults to None so a CLI/eval caller keeps
    its current per-call load behavior unchanged.

    `timing`/`usage`, if given, get populated with real per-stage latency
    and real Groq token usage for any rewrite_query call made.
    """
    if resources is not None:
        dense_model = resources["dense_model"]
        qdrant_client = resources["qdrant_client"]
        bm25_index = resources["bm25_index"]
        bm25_chunks = resources["bm25_chunks"]
        cross_encoder = resources["cross_encoder"]
    else:
        dense_model = SentenceTransformer(EMBEDDING_MODEL)
        qdrant_client = get_qdrant_client()
        bm25_index, bm25_chunks = build_bm25_index(Path("data/raw"))
        cross_encoder = get_cross_encoder()

    chunks, full_pool = search_hybrid(
        query, qdrant_client, dense_model, bm25_index, bm25_chunks, cross_encoder,
        product_ins_codes=product_ins_codes, top_k=top_k, return_full_pool=True, timing=timing,
        intent=intent,
    )
    top_score = chunks[0]["rerank_score"] if chunks else 0.0

    if top_score >= RERANK_SCORE_THRESHOLD:
        return _trim_to_corroborated_chunks(chunks)

    if chunks and _has_bm25_consensus(full_pool, chunks[0]["chunk_id"]):
        if verbose:
            print(f"\nTop rerank score {top_score:.3f} below threshold, but the top pick shows a "
                  f"landslide BM25 consensus — skipping the corrective retry.\n")
        return _trim_to_corroborated_chunks(chunks)

    if verbose:
        print(f"\nTop rerank score {top_score:.3f} below threshold {RERANK_SCORE_THRESHOLD} — retrying with rewritten query\n")
    with timed(timing, "query_rewrite"):
        rewritten_query = rewrite_query(query, usage_out=usage)
    if verbose:
        print(f"Rewritten query: {rewritten_query!r}\n")

    retry_chunks, retry_full_pool = search_hybrid(
        rewritten_query, qdrant_client, dense_model, bm25_index, bm25_chunks, cross_encoder,
        product_ins_codes=product_ins_codes, top_k=top_k, return_full_pool=True, timing=timing,
        intent=intent,
    )
    retry_score = retry_chunks[0]["rerank_score"] if retry_chunks else 0.0

    if retry_score >= RERANK_SCORE_THRESHOLD:
        return _trim_to_corroborated_chunks(retry_chunks)

    # Narrow, evidence-based override, checked only now — after BOTH the
    # original and retried query have failed to clear the threshold. Checks
    # the retry's pool first, then falls back to the original query's pool,
    # since a query rewrite can occasionally lose a pairing that was present
    # in the original query's own pool.
    comparison_match = find_comparison_group_match(retry_full_pool, top_k=top_k) \
        or find_comparison_group_match(full_pool, top_k=top_k)
    if comparison_match is not None:
        if verbose:
            print(f"\nRetry score {retry_score:.3f} still below threshold, but found a tagged "
                  f"comparison_group match — bypassing the confidence gate.\n")
        return rerank(rewritten_query, comparison_match, cross_encoder, top_k=top_k)

    if verbose:
        print(f"Retry score {retry_score:.3f} still below threshold — insufficient-evidence.\n")
    return None


def _sync_product_into_state(state: dict, product_id: str | None, conn) -> None:
    """
    Keeps conversation_state's product_id/product_name aligned with whatever
    routing just resolved. No-ops if nothing resolved this turn.
    conversation/state.py::set_product() itself resets known_facts only when
    the product genuinely changes, so a same-product call here is always
    safe to make unconditionally.
    """
    if not product_id:
        return
    row = get_product_row(product_id, conn)
    if row is not None:
        set_product(state, product_id, row["name"])
