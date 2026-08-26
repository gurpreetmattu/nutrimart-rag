"""
eval/faithfulness_score.py — a pure, cheap numeric-claim-support score used
by api/main.py's `_confidence_breakdown()` to show a UI "claim support"
figure without a second LLM call.

Reuses generation/groundedness.py's citation-parsing and numeric-checking
internals directly (chunk-matching, claim-splitting) rather than a second
implementation, since check_groundedness() already computes everything
needed here as a side effect of its own annotation pass.
"""
from generation.groundedness import (
    CHECKED_TAGS,
    UNVERIFIED_MARKER,
    _extract_citations,
    _match_chunks,
    _numeric_tokens,
    _split_claims,
    check_groundedness,
)


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
