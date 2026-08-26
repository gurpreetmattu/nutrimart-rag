"""
search_hybrid.py — the hybrid retriever: BM25 + dense fusion, doc_type
intent boost, ingredient-entity scoping, cross-encoder rerank.

Called from hybrid_core.py::retrieve_hybrid_with_retry(), which
ask_langchain_hybrid.py depends on for its full hybrid retrieval path
(ask_langchain.py's own naive pipeline uses a separate, simpler
dense-only retriever instead — see its own docstring).

Every filtering step here is deliberately inclusive-by-default — see
ingestion/parse_kb.py's preamble-default fix: most of the KB's doc_type/
entity metadata is thin or missing, so a chunk is only ever excluded when
there's specific,
confirmable evidence it doesn't belong (a different INS code than
anything in the resolved product) — never on an unmatched or absent
signal.
"""
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from qdrant_client import QdrantClient
from sentence_transformers import CrossEncoder, SentenceTransformer

from config import COLLECTION_NAME, BGE_QUERY_PREFIX
from ingestion.parse_kb import Chunk
from retrieval.bm25_index import bm25_search
from retrieval.rerank import rerank
from routing.query_router import classify_doc_type, INTENT_DOC_TYPE_POLICY


def _accumulate(timing: dict | None, key: str, duration: float) -> None:
    if timing is not None:
        timing[key] = timing.get(key, 0.0) + duration

RRF_K = 60  # standard Reciprocal Rank Fusion constant
DOC_TYPE_BOOST = 1 / RRF_K  # roughly one extra rank-1 vote's worth of score
FUSION_POOL_SIZE = 20   # top-N pulled from each of dense/BM25 before fusion
RERANK_POOL_SIZE = 15   # top-N fused candidates handed to the cross-encoder

# Functional-class boost (added 2026-08-25, real gap found via the RAGAS
# eval, q22/q23): the ins_no exclusion filter below is evidence-based but
# EXCLUSION-only — it drops a candidate only when its ins_no ISN'T among
# the product's declared codes, it never boosts the SPECIFIC class the
# question actually asked about. A product declaring several INS-coded
# ingredients across different functional classes (Yippee: thickeners,
# acidity regulators, a flavour enhancer, an anticaking agent, ...) means
# a query like "the flavour enhancer... permitted limit" competes against
# ALL of that product's declared-ingredient chunks roughly equally, since
# none of them get excluded (they're all genuinely present) and nothing
# boosts the one class actually asked about. Confirmed real: q23 retrieved
# Chunk 40 (anticaking) and three unrelated carbonate/gum entries — all
# genuinely declared by the product, all irrelevant to the actual
# question — while the real target (INS 627/631/635, flavour enhancers)
# never won the ranking.
#
# _CLASS_INS_INDEX is built from ingredient_knowledge_base.md's own real
# `##` section structure (Preservatives, Acidity Regulators, Flavour
# Enhancers, ...) — not a hand-typed duplicate list, same reasoning as
# product_facts.py's _get_ins_name_index() for the sulphite/dough-
# conditioner fix. _QUERY_CLASS_TERMS maps a few common lay phrasings to
# those same canonical section names; deliberately a short, closed list
# (functional-additive classes are a small, stable vocabulary, not an
# open-ended judgment-word set — same reasoning as _REGULATORY_LIMIT_RE/
# _CLAIM_ELIGIBILITY_RE in ask_hybrid.py).
_QUERY_CLASS_TERMS: dict[str, str] = {
    "flavour enhancer": "Flavour Enhancers",
    "flavor enhancer": "Flavour Enhancers",
    "anticaking agent": "Anticaking / Flour Treatment",
    "anti-caking agent": "Anticaking / Flour Treatment",
    "colour additive": "Colours",
    "color additive": "Colours",
    "colour": "Colours",
    "color": "Colours",
    "emulsifier": "Emulsifiers / Stabilizers / Thickeners",
    "stabilizer": "Emulsifiers / Stabilizers / Thickeners",
    "stabiliser": "Emulsifiers / Stabilizers / Thickeners",
    "thickener": "Emulsifiers / Stabilizers / Thickeners",
    "acidity regulator": "Acidity Regulators",
    "raising agent": "Raising Agents / Alkalis",
    "preservative": "Preservatives",
    "antioxidant": "Antioxidants",
    "sweetener": "Sweeteners",
}

_CLASS_INS_INDEX: dict[str, set[str]] | None = None


def _get_class_ins_index() -> dict[str, set[str]]:
    """
    Maps each real functional-class section name in
    ingredient_knowledge_base.md (e.g. "Flavour Enhancers") to the real
    INS codes listed under it (e.g. {"627", "631", "635"}) — built once by
    walking the file's own `##`/`###` heading structure directly (cheap,
    pure text parsing, no model/Qdrant cost), not a second hand-maintained
    copy of the same grouping.
    """
    global _CLASS_INS_INDEX
    if _CLASS_INS_INDEX is not None:
        return _CLASS_INS_INDEX

    import re

    from structured.product_ingredients import INS_CODE_RE

    index: dict[str, set[str]] = {}
    path = Path("data/raw/ingredient_knowledge_base.md")
    current_class: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        h2 = re.match(r"^##\s+(.+)$", line)
        if h2:
            current_class = h2.group(1).strip()
            continue
        h3 = re.match(r"^###\s+(.+)$", line)
        if h3 and current_class:
            for code in INS_CODE_RE.findall(h3.group(1).lower()):
                index.setdefault(current_class, set()).add(code)

    _CLASS_INS_INDEX = index
    return index


def _ins_codes_of(ins_no: str) -> set[str]:
    """
    Splits a chunk's raw `ins_no` field into individual codes — it can be
    a compound string for a multi-code entry (e.g. "627/631/635",
    confirmed real for the flavour-enhancer group entry; also
    "450(i), 451(i), 452(i)" for the diphosphates entry). Every ins_no
    comparison in this module (the class boost, the exclusion filter, the
    injection step) needs this same split — a bare `"627/631/635" in
    {"627", "631"}` is always False even when the chunk genuinely covers
    a declared code, which is exactly the real bug found 2026-08-25 (q23):
    the exclusion filter was silently dropping this exact chunk from the
    candidate pool even though it was already fused with a legitimate,
    competitive score, because of this unsplit comparison.
    """
    return {c.strip() for c in re.split(r"[,/]", ins_no) if c.strip()}


def _detect_query_class(query: str) -> str | None:
    q = query.lower()
    # Longest phrase first, so e.g. "colour additive" (if ever ambiguous
    # against a shorter key) matches its more specific entry.
    for phrase in sorted(_QUERY_CLASS_TERMS, key=len, reverse=True):
        if phrase in q:
            return _QUERY_CLASS_TERMS[phrase]
    return None


def _dense_search(query: str, client: QdrantClient, model: SentenceTransformer, top_n: int) -> list[dict]:
    query_vector = model.encode(BGE_QUERY_PREFIX + query, normalize_embeddings=True).tolist()
    results = client.query_points(collection_name=COLLECTION_NAME, query=query_vector, limit=top_n).points
    return [
        {
            "chunk_id": r.payload["chunk_id"],
            "source_file": r.payload["source_file"],
            "heading": r.payload["heading"],
            "text": r.payload["text"],
            "doc_type": r.payload["doc_type"],
            "entity": r.payload.get("entity", ""),
            "ins_no": r.payload.get("ins_no", ""),
            "comparison_group": r.payload.get("comparison_group", ""),
        }
        for r in results
    ]


def _chunk_to_dict(chunk: Chunk) -> dict:
    return {
        "chunk_id": chunk.chunk_id,
        "source_file": chunk.source_file,
        "heading": chunk.heading,
        "text": chunk.text,
        "doc_type": chunk.doc_type,
        "entity": chunk.entity,
        "ins_no": chunk.ins_no,
        "comparison_group": chunk.comparison_group,
    }


def _fuse(dense_results: list[dict], bm25_results: list[tuple[Chunk, float]]) -> dict[str, dict]:
    """
    Reciprocal Rank Fusion by chunk_id. Returns {chunk_id: chunk_dict}
    with an "rrf_score" key added to each dict.

    Also carries a "bm25_score" key (added 2026-08-25 for the q27
    corrective-retry fix, PHASE3_TESTING_LOG.md Finding 31/33) — the raw,
    un-fused BM25 score from `bm25_search`, not the rank-based RRF
    contribution. `ask_hybrid.py::retrieve_hybrid_with_retry()` uses this
    as an independent corroborating signal: the cross-encoder's own
    absolute rerank score is a known-uncalibrated confidence gate (Finding
    31), but a landslide raw BM25 margin between the top pick and #2 is a
    real, separately-sourced signal the retry logic can trust even when
    the cross-encoder score alone can't be. Defaults to 0.0 for a chunk
    that only ever came from dense search (never matched in BM25 at all).
    """
    fused: dict[str, dict] = {}

    for rank, d in enumerate(dense_results):
        fused.setdefault(d["chunk_id"], dict(d))
        entry = fused[d["chunk_id"]]
        entry["rrf_score"] = entry.get("rrf_score", 0.0) + 1 / (RRF_K + rank)
        entry.setdefault("bm25_score", 0.0)

    for rank, (chunk, score) in enumerate(bm25_results):
        cid = chunk.chunk_id
        if cid not in fused:
            fused[cid] = _chunk_to_dict(chunk)
            fused[cid]["rrf_score"] = 0.0
        fused[cid]["rrf_score"] += 1 / (RRF_K + rank)
        fused[cid]["bm25_score"] = max(fused[cid].get("bm25_score", 0.0), score)

    return fused


def find_comparison_group_match(candidates: list[dict], top_k: int = 5) -> list[dict] | None:
    """
    Narrow, evidence-based override for ask_hybrid.py's corrective-retry
    confidence gate (see that module's retrieve_hybrid_with_retry): looks
    for 2+ candidates in the fused pool sharing the same non-empty
    comparison_group tag — a curated, deliberately-authored pairing
    written directly into the KB (e.g. "sugar_vs_sweetener" links
    fssai_knowledge_base.md Chunk 5 and nutrition_knowledge_base.md
    Chunk 8c). This exists because a real case (q07-style "should I pick
    the diet version instead of regular") was verified to have both
    relevant chunks already reaching the fused candidate pool, but neither
    individually clearing RERANK_SCORE_THRESHOLD on its own — the
    threshold gate has no way to say "no single chunk is confident, but
    together these two known comparison sides answer the question."

    Only ever activates on a real tag match — never guesses at a pairing
    that isn't explicitly authored into the KB, matching this module's
    inclusive-by-default-but-evidence-gated philosophy everywhere else
    (see the ingredient-entity exclusion above, which is the mirror case:
    excluded only on confirmed evidence; this is included past the
    confidence gate only on confirmed evidence).

    Requires the matched chunks to span 2+ distinct source_file values —
    found as a real false-positive bug 2026-08-18: q09 ("why does this
    ketchup need a preservative") pulled both nutrition_knowledge_base.md
    Chunk 8a and Chunk 8c into its pool (both carry comparison_group=
    "sugar_vs_sweetener", loosely nutrition-topic-adjacent, but neither
    actually relevant to preservatives) and got wrongly treated as a valid
    comparison match. A real comparison pairing (like sugar_vs_sweetener's
    actual intended use — an FSSAI regulatory chunk vs. a WHO nutrition
    chunk) spans two different KB documents by design; two same-file
    chunks sharing a tag is weaker, coincidental evidence, not proof of a
    real cross-document comparison the query is actually asking about.
    """
    groups: dict[str, list[dict]] = {}
    for c in candidates:
        tag = c.get("comparison_group")
        if tag:
            groups.setdefault(tag, []).append(c)

    for group_chunks in groups.values():
        distinct_files = {c["source_file"] for c in group_chunks}
        if len(group_chunks) >= 2 and len(distinct_files) >= 2:
            return group_chunks[:top_k]
    return None


def search_hybrid(
    query: str,
    qdrant_client: QdrantClient,
    dense_model: SentenceTransformer,
    bm25_index,
    bm25_chunks: list[Chunk],
    cross_encoder: CrossEncoder,
    product_ins_codes: set[str] | None = None,
    top_k: int = 5,
    return_full_pool: bool = False,
    timing: dict | None = None,
    intent: str | None = None,
) -> list[dict] | tuple[list[dict], list[dict]]:
    """
    If return_full_pool is True, returns (reranked_top_k, full_candidate_pool)
    instead of just reranked_top_k — the full pre-rerank-cutoff candidate
    pool is what ask_hybrid.py's comparison_group override needs to see,
    since chunks relevant to one side of a tagged comparison may not
    individually clear the rerank score threshold but still be present in
    the wider pool before it's cut down to RERANK_POOL_SIZE and reranked.

    `timing`, if given, gets `dense_search`/`bm25_search`/`rerank` durations
    ADDED to (via `_accumulate`, not overwritten) — a corrective retry calls
    this function twice (see ask_hybrid.py), so the two calls' durations per
    stage are summed into one real end-to-end figure, not one overwriting
    the other. Optional, default None, no behavior change for any existing
    caller.

    `intent`, if given (one of routing/query_router.py::classify_intent()'s
    categories), applies INTENT_DOC_TYPE_POLICY's boost/penalize doc_type
    lists — a stronger, multi-doc_type version of the existing single-hint
    classify_doc_type() boost below (problems.md Problem 2/3: regulatory
    chunks overpowering nutrition questions). Still a soft RRF adjustment,
    never a hard filter — see the module docstring on why. Falls back to
    the existing classify_doc_type() single-hint boost when `intent` isn't
    passed or isn't in the policy table — zero behavior change for any
    caller that doesn't opt in (ask.py's baseline never will).
    """
    start = time.perf_counter()
    dense_results = _dense_search(query, qdrant_client, dense_model, FUSION_POOL_SIZE)
    _accumulate(timing, "dense_search", time.perf_counter() - start)

    start = time.perf_counter()
    bm25_results = bm25_search(bm25_index, bm25_chunks, query, FUSION_POOL_SIZE)
    _accumulate(timing, "bm25_search", time.perf_counter() - start)

    fused = _fuse(dense_results, bm25_results)

    doc_type_hint = classify_doc_type(query)
    intent_policy = INTENT_DOC_TYPE_POLICY.get(intent) if intent else None

    # Functional-class boost (see _get_class_ins_index's docstring above)
    # — only computed when a product is actually resolved, since it's
    # meaningless without product_ins_codes to intersect against.
    class_boost_codes: set[str] = set()
    if product_ins_codes:
        query_class = _detect_query_class(query)
        if query_class:
            class_boost_codes = _get_class_ins_index().get(query_class, set()) & product_ins_codes

    # Evidence-based forced inclusion (added 2026-08-25, real gap: q23):
    # the boost above only helps a chunk that BM25/dense already pulled
    # into `fused` — confirmed real that this isn't always true (Yippee's
    # "INS 627/631/635" flavour-enhancer chunk never made either side's
    # own top-20 for "is the flavour enhancer... within FSSAI's permitted
    # limit", so there was nothing in the pool for the boost to act on).
    # Mirrors the exclusion filter below's own evidence-based framing,
    # just flipped from removal to insertion: when we already KNOW (from
    # the product's real declared INS codes, same evidence the exclusion
    # filter uses) that a specific KB chunk matches the class the query
    # asked about, splice it directly into the fused pool from `bm25_chunks`
    # (already in memory, no extra I/O) rather than leaving its presence
    # to BM25/dense ranking chance. Deliberately does NOT hand it a
    # privileged score — it's seeded at the current lowest fused rrf_score
    # (or 0.0 if the pool is empty) so it competes through the SAME
    # cross-encoder reranking as everything else; injection guarantees a
    # fair shot at being considered, never guarantees the final answer,
    # same "boost, don't force" discipline as the doc_type/class boosts
    # (Finding 7: hard-filtering on this KB's thin metadata backfired once
    # already). Capped at 3 injected chunks — a functional class spanning
    # many codes (e.g. Emulsifiers/Stabilizers/Thickeners has 9) shouldn't
    # be allowed to flood the rerank pool just because a product happens
    # to declare several of them.
    if class_boost_codes:
        floor_score = min((c["rrf_score"] for c in fused.values()), default=0.0)
        injected = 0
        for chunk in bm25_chunks:
            if injected >= 3:
                break
            if not chunk.ins_no or chunk.chunk_id in fused:
                continue
            if _ins_codes_of(chunk.ins_no) & class_boost_codes:
                fused[chunk.chunk_id] = _chunk_to_dict(chunk)
                fused[chunk.chunk_id]["rrf_score"] = floor_score
                injected += 1

    candidates = []
    for c in fused.values():
        if intent_policy:
            if c["doc_type"] in intent_policy["boost"]:
                c["rrf_score"] += DOC_TYPE_BOOST
            elif c["doc_type"] in intent_policy["penalize"]:
                c["rrf_score"] -= DOC_TYPE_BOOST / 2
        elif doc_type_hint and c["doc_type"] == doc_type_hint:
            c["rrf_score"] += DOC_TYPE_BOOST

        if class_boost_codes and c["ins_no"] and _ins_codes_of(c["ins_no"]) & class_boost_codes:
            c["rrf_score"] += DOC_TYPE_BOOST

        # Narrow, evidence-based exclusion: only drop a chunk when we know
        # which product this query is about AND the chunk is unambiguously
        # about one specific, different INS-coded additive. Everything else
        # (no product resolved, chunk has no ins_no, non-ingredient
        # doc_type) passes through untouched.
        #
        # Compares SPLIT codes (via _ins_codes_of), not the raw ins_no
        # string — fixed 2026-08-25, a real bug found alongside the class-
        # boost work: a multi-code entry's ins_no (e.g. "627/631/635")
        # never equals any single code in product_ins_codes as a whole
        # string, so this filter was silently excluding every multi-code
        # chunk whose product genuinely declared one of its codes — the
        # actual root cause of q23's retrieval miss, not a ranking problem
        # at all. Excludes only when NONE of the chunk's codes match.
        if (
            product_ins_codes is not None
            and c["doc_type"] in ("ingredient", "ingredient_general")
            and c["ins_no"]
            and not (_ins_codes_of(c["ins_no"]) & product_ins_codes)
        ):
            continue

        # Second, narrower exclusion (added 2026-08-25, Finding 36 — a real
        # context_precision gap found via the RAGAS harness on q21-q24):
        # when a query names a SPECIFIC functional class ("the colour
        # additive", "the flavour enhancer") AND the product declares
        # several genuinely-real ingredients across DIFFERENT classes, the
        # cross-encoder scores every one of those other declared-ingredient
        # chunks almost as highly as the correct one (confirmed real: all
        # 0.94-0.99 for Kurkure's colour-additive question, since they all
        # read as similarly-shaped "INS ### — permitted limit" text) — the
        # class boost above helps the RIGHT chunk win the ranking, but
        # doesn't stop the WRONG-class ones from still reaching generation
        # at a "confident" score, hurting context_precision even though
        # faithfulness/recall are unaffected (they're correctly never
        # cited). This reuses the SAME evidence the boost above already
        # computed (class_boost_codes: the specific codes both matching the
        # query's class AND genuinely declared by this product) — only
        # excludes a chunk that IS a real declared ingredient (already
        # passed the check above) but belongs to a DIFFERENT class than the
        # one the query actually asked about. Only fires when a query class
        # was confidently detected (class_boost_codes non-empty) — same
        # "only exclude on confirmed evidence" discipline as the exclusion
        # above, never a guess.
        if (
            class_boost_codes
            and c["doc_type"] in ("ingredient", "ingredient_general")
            and c["ins_no"]
            and not (_ins_codes_of(c["ins_no"]) & class_boost_codes)
        ):
            continue

        candidates.append(c)

    candidates.sort(key=lambda c: c["rrf_score"], reverse=True)
    pool = candidates[:RERANK_POOL_SIZE]

    start = time.perf_counter()
    reranked = rerank(query, pool, cross_encoder, top_k=top_k)
    _accumulate(timing, "rerank", time.perf_counter() - start)

    if return_full_pool:
        return reranked, candidates
    return reranked


if __name__ == "__main__":
    from config import get_qdrant_client, EMBEDDING_MODEL
    from retrieval.bm25_index import build_bm25_index
    from retrieval.rerank import get_cross_encoder

    query = sys.argv[1] if len(sys.argv) > 1 else "is aspartame safe in Diet Coke"
    raw_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("data/raw")

    print("Loading models/index...")
    client = get_qdrant_client()
    dense_model = SentenceTransformer(EMBEDDING_MODEL)
    bm25_index, bm25_chunks = build_bm25_index(raw_dir)
    cross_encoder = get_cross_encoder()

    print(f"\nQuery: {query!r}\n{'-'*60}")
    results = search_hybrid(query, client, dense_model, bm25_index, bm25_chunks, cross_encoder, top_k=5)
    for i, r in enumerate(results, 1):
        print(f"[{i}] rerank={r['rerank_score']:.3f} rrf={r['rrf_score']:.4f}  {r['source_file']} -- {r['heading']}")
