"""
api/response_helpers.py — pure, pipeline-agnostic response-shaping logic
shared between api/main.py (ask_hybrid.py) and api/main_langchain.py
(ask_langchain_hybrid.py).

Split out 2026-08-24 after an audit found `_confidence()`/`_build_sources()`
had been hand-copied into api/main_langchain.py instead of imported —
main.py's version correctly treats `product_fact` and `product_comparison`
both as instant/no-LLM-involved routes (see `_confidence()`'s own comment),
but the copy in main_langchain.py only special-cased `product_fact`,
silently mislabeling a structured comparison answer as "uncertain" even
though it involved no retrieval and carries no hallucination risk. Neither
function has any pipeline-specific dependency (both only need `route` and
`chunks`, whatever produced them), so there was never a reason for two
copies to exist — sharing one definition means a future fix here can't
silently diverge between the two API apps again.
"""
import re

from hybrid_core import RERANK_SCORE_THRESHOLD
from generation.groundedness import _extract_citations, _match_chunks
from pydantic import BaseModel

_MD_HEADING_RE = re.compile(r"^#{1,6}\s*", re.MULTILINE)
_MD_BOLD_RE = re.compile(r"\*\*(.+?)\*\*")


class Source(BaseModel):
    source_file: str
    heading: str
    doc_type: str
    snippet: str


# Confidence tier surfaced in the UI next to the route badge, derived from
# the real cross-encoder rerank score the answer was actually generated
# from (chunks[0]["rerank_score"]) — not a separate/fabricated number.
# "high" cutoff (2x RERANK_SCORE_THRESHOLD) is an uncalibrated first guess,
# same status as RERANK_SCORE_THRESHOLD itself and the routing keyword
# lists — not validated against a real score distribution yet.
def _confidence(route: str, chunks: list[dict] | None) -> tuple[str, float | None]:
    if route in ("product_fact", "product_comparison"):
        # Both are direct SQL lookups, no LLM/retrieval involved — same
        # "instant" tier product_fact already used, not "uncertain" just
        # because chunks is None (product_comparison never has any).
        return "instant", None
    if not chunks:
        return "uncertain", None
    top_score = chunks[0].get("rerank_score", 0.0)
    if top_score >= RERANK_SCORE_THRESHOLD * 2:
        tier = "high"
    elif top_score >= RERANK_SCORE_THRESHOLD:
        tier = "medium"
    else:
        # Only reachable via the comparison_group override path
        # (retrieve_hybrid_with_retry), which returns real chunks despite
        # both attempts scoring below threshold.
        tier = "low"
    return tier, round(top_score, 3)


def _build_sources(answer: str, chunks: list[dict] | None) -> list[Source]:
    """
    Reuses groundedness.py's own citation-parsing internals (the same
    "(source_file.md, heading)" parser it uses to check groundedness) to
    find exactly the chunks the answer actually cites, rather than
    dumping every retrieved-but-possibly-unused candidate. eval/phase7_metrics.py
    already reuses these same internals for citation-accuracy scoring — this
    follows the same established pattern instead of re-deriving the parsing.
    """
    if not chunks:
        return []
    citations = _extract_citations(answer, chunks=chunks)
    matched = _match_chunks(citations, chunks)

    seen = set()
    sources = []
    for c in matched:
        if c["chunk_id"] in seen:
            continue
        seen.add(c["chunk_id"])
        snippet = _MD_HEADING_RE.sub("", c["text"].strip())
        snippet = _MD_BOLD_RE.sub(r"\1", snippet).strip()
        if len(snippet) > 320:
            snippet = snippet[:320].rsplit(" ", 1)[0] + "…"
        sources.append(Source(
            source_file=c["source_file"],
            heading=c["heading"],
            doc_type=c.get("doc_type", ""),
            snippet=snippet,
        ))
    return sources
