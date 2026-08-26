"""
phase7_metrics.py — pure scoring functions for the Phase 7 naive-vs-hybrid
comparison (run_phase7_comparison.py). No I/O here on purpose: these take
already-fetched chunks/answers and return numbers, so they're testable
against synthetic cases without Qdrant/Groq.

Reuses generation/groundedness.py's citation-parsing and numeric-checking
internals directly — they're generic (chunk-matching, claim-splitting)
despite that module only being wired into ask_hybrid.py for production use.
Calling check_groundedness() here on baseline's answers is a measurement-
only use, not a change to ask.py's behavior.
"""
from generation.groundedness import (
    ALL_TAGS,
    CHECKED_TAGS,
    UNVERIFIED_MARKER,
    _extract_citations,
    _match_chunks,
    _numeric_tokens,
    _split_claims,
    check_groundedness,
)


def recall_at_k(retrieved: list[dict], ground_truth: list[tuple[str, str]], k: int) -> float:
    """Fraction of ground_truth (source_file, heading_prefix) pairs found
    anywhere in retrieved[:k], matching heading by prefix (see
    test_questions.py's module docstring for why prefix, not equality)."""
    if not ground_truth:
        return None
    top_k = retrieved[:k]
    found = 0
    for source_file, heading_prefix in ground_truth:
        if any(
            c.get("source_file") == source_file and c.get("heading", "").startswith(heading_prefix)
            for c in top_k
        ):
            found += 1
    return found / len(ground_truth)


def reciprocal_rank(retrieved: list[dict], ground_truth: list[tuple[str, str]]) -> float:
    """1/rank of the first chunk matching ANY ground_truth pair, 0.0 if none found."""
    if not ground_truth:
        return None
    for rank, c in enumerate(retrieved, 1):
        for source_file, heading_prefix in ground_truth:
            if c.get("source_file") == source_file and c.get("heading", "").startswith(heading_prefix):
                return 1.0 / rank
    return 0.0


def citation_accuracy(answer: str, chunks: list[dict]) -> float:
    """Fraction of citations in answer that resolve to a real chunk in chunks.
    None if the answer has no citations to check."""
    blocks = _split_claims(answer)
    total = 0
    resolved = 0
    for tag, block_text in blocks:
        if tag not in ALL_TAGS:
            continue
        citations = _extract_citations(block_text, chunks=chunks)
        for citation in citations:
            total += 1
            if _match_chunks([citation], chunks):
                resolved += 1
    if total == 0:
        return None
    return resolved / total


def faithfulness_score(answer: str, chunks: list[dict]) -> tuple[int, int]:
    """(checked, flagged) counts from the numeric-consistency groundedness
    check. checked=0 means no numeric-bearing checkable claim was found —
    faithfulness is undefined (not 1.0) for that answer."""
    annotated = check_groundedness(answer, chunks)
    flagged = annotated.count(UNVERIFIED_MARKER)

    checked = 0
    for tag, block_text in _split_claims(answer):
        if tag not in CHECKED_TAGS:
            continue
        citations = _extract_citations(block_text, chunks=chunks)
        if not citations or not _match_chunks(citations, chunks):
            # No citation, or citation didn't resolve to a real chunk —
            # check_groundedness() itself skips (fail-open) in this case
            # rather than flagging, so it must not count as "checked"
            # either, or an unresolved citation would misleadingly look
            # like a verified-faithful claim (checked=1, flagged=0).
            continue
        hypothesis = block_text
        for check_tag in CHECKED_TAGS:
            hypothesis = hypothesis.replace(f"[{check_tag}]", "")
        if _numeric_tokens(hypothesis):
            checked += 1

    return checked, flagged


def routing_match(actual_route: str, actual_product_id: str | None, actual_fact_field: str | None, question: dict) -> bool | None:
    """Compares actual routing output against a question's expected_route/
    expected_product_id/expected_fact_field. None if the question doesn't
    specify expected_route (i.e. it's not a routing test case)."""
    expected_route = question.get("expected_route")
    if expected_route is None:
        return None
    if actual_route != expected_route:
        return False
    if "expected_product_id" in question and actual_product_id != question["expected_product_id"]:
        return False
    if "expected_fact_field" in question and actual_fact_field != question["expected_fact_field"]:
        return False
    return True
