"""
groundedness.py — post-generation check: does each cited claim in a
generated answer actually hold up against the chunk it cites?

The corrective retry that already exists (llm.py::rewrite_query) catches
weak *retrieval* before generation; this catches a *generated* claim that
isn't actually supported by its own cited source, which the retry has no
visibility into.

Scope: this verifies "is this claim entailed by the chunk it cites," not
"do multiple retrieved chunks conflict with each other" (a separate,
still-open item). A claim whose own cited source genuinely supports it
will pass here even if another retrieved chunk states a different number.

[UNCERTAIN] claims assert nothing to verify, and [DERIVED CALCULATION]
claims are computed values not expected to be literally entailed by source
text — both are skipped rather than checked, to avoid false positives.

**Numeric claims only, by design — not general NLI.** Three different NLI
approaches (cross-encoder/nli-MiniLM2-L6-H768, same sentence_transformers
pattern as retrieval/rerank.py) were tried and reverted: whole-chunk
entailment, per-sentence any-contradiction, and whole-chunk contradiction.
Each produced real false positives when verified against this KB's actual
long, multi-topic technical chunks — including flagging claims that were
near-verbatim restatements of their cited source. A general-purpose small
NLI model just isn't reliable enough on this domain to be worth the false
positives. What IS reliable, verified directly: this KB's real
hallucination risk is dominated by wrong regulatory numbers (ppm/%/mg-kg
limits), and a literal numeric-token check for those works cleanly. So
that's the whole check — a claim with a number must have that exact number
appear in its cited chunk, or it's flagged; a claim with no number passes
unchecked. This is a known, deliberate limitation, not an oversight: a
non-numeric hallucination (a fabricated non-numeric fact) won't be caught.
"""
import difflib
import re

CHECKED_TAGS = ("FACT", "REGULATORY", "INTERPRETATION")
SKIPPED_TAGS = ("UNCERTAIN", "DERIVED CALCULATION")
ALL_TAGS = CHECKED_TAGS + SKIPPED_TAGS

# Splits the answer into (tag, block_text_including_tag) pieces, one per
# claim. Matches ANY bracketed all-caps-ish token, not just an exact
# ALL_TAGS string — confirmed real 2026-08-20: the generation model wrote
# "[INTERPRETION]" (missing "TA"), which an exact-list regex doesn't
# match at all, so the whole block silently fell into the untagged
# passthrough: not groundedness-checked, and (via consumer_view.py, which
# used to build its own exact-list regex too) not stripped from the
# consumer-facing answer either — the raw bracket leaked straight to the
# UI. TAG_RE now matches the bracket shape generically and _split_claims
# normalizes the captured word to its closest ALL_TAGS entry, so a typo'd
# tag still gets stripped and still gets checked as the tag it was
# obviously meant to be.
TAG_RE = re.compile(r"\[([A-Z][A-Z \-]{1,40})\]")


def _normalize_tag(raw: str) -> str:
    raw = raw.strip()
    if raw in ALL_TAGS:
        return raw
    close = difflib.get_close_matches(raw, ALL_TAGS, n=1, cutoff=0.6)
    return close[0] if close else raw

# A citation group is one or more "(file, ref)" mentions, semicolon- or
# comma-separated within a single parens, e.g.
# "(fssai_knowledge_base.md, Chunk 50; ingredient_knowledge_base.md, INS 951 — Aspartame)"
# Handles one level of nested parens inside the citation ref itself (e.g.
# "(ingredient_knowledge_base.md, INS 307b — Mixed Tocopherols (Vitamin E))"
# — a real, common shape for ingredient KB entry names). The naive
# "\(([^()]+)\)" only ever matched the INNERMOST "(Vitamin E)" here since
# it can't cross a nested "(", leaving the outer citation — filename
# included — completely unstripped and leaking straight into the
# consumer-facing view (confirmed real 2026-08-21, Kellogg's Chocos "is
# this a good breakfast" answer). One level of nesting covers every real
# case seen in this KB; deeper nesting doesn't occur in these headings.
CITATION_GROUP_RE = re.compile(r"\(([^()]*(?:\([^()]*\)[^()]*)*)\)")
# Ref group (group 2) deliberately allows parens now — real chunk/entry
# names commonly contain them (e.g. "INS 307b — Mixed Tocopherols (Vitamin
# E))"). Without this the ref matched but was silently truncated right
# before the first "(" (Python's .match() doesn't require consuming the
# whole string, so the truncated match still "succeeded"), which is enough
# to make CITATION_GROUP_RE-based stripping work but corrupts any caller
# that needs the FULL ref text to match a real chunk heading (sources
# panel, groundedness citation verification) — confirmed real 2026-08-21.
CITATION_PART_RE = re.compile(r"([^,;()]+\.\w+),\s*(.+)")

UNVERIFIED_MARKER = " ⚠️ [UNVERIFIED — not clearly supported by cited source]"

# This KB's hallucination risk is dominated by wrong regulatory numbers
# (ppm/%/mg-kg limits), and a literal-token check for those is far more
# reliable than NLI on this domain (see check_groundedness's design note).
#
# The digit group allows an optional thousands separator (a space or comma
# every 3 digits, e.g. "3 500" or "3,500") before the decimal part — found
# as a real false-positive bug 2026-08-18: the current generation model
# sometimes writes "3 500 ppm" for a number the source chunk states as
# "3500 ppm" (same value, different formatting), which the original
# digits-only pattern didn't recognize as the same token, flagging a
# correctly-grounded claim as unverified.
_NUMERIC_TOKEN_RE = re.compile(
    r"\b(?:\d{1,3}(?:[,\s]\d{3})+|\d+)(?:\.\d+)?\s?(?:%|ppm|mg/kg|mg|kcal|g)(?!\w)", re.IGNORECASE
)


def _split_claims(answer: str) -> list[tuple[str | None, str]]:
    """
    Splits `answer` into (tag, block_text) pairs. `tag` is None for any
    leading text before the first tag (e.g. a bare restatement) — passed
    through unchanged, never checked.
    """
    matches = list(TAG_RE.finditer(answer))
    if not matches:
        return [(None, answer)]

    blocks = []
    if matches[0].start() > 0:
        blocks.append((None, answer[: matches[0].start()]))

    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(answer)
        blocks.append((_normalize_tag(m.group(1)), answer[m.start():end]))

    return blocks


# Recovers a citation the model wrote using the internal "Source N" prompt
# label (build_context_block() in llm.py assigns "[Source N: file, heading]"
# to each retrieved chunk, 1-indexed) instead of the required real filename
# — SYSTEM_PROMPT explicitly tells it not to, but compliance isn't 100%.
# Different failure shape than _SOURCE_PREFIX_RE above (that one strips a
# "Source N:" prefix GLUED ONTO an otherwise-real filename; this one covers
# the model replacing the filename with "Source N" entirely, e.g.
# "(Source 2, Chunk 1)") — CITATION_PART_RE never matches that at all (group
# 1 requires a real "file.ext" shape), so _extract_citations() used to just
# silently drop it, confirmed real 2026-08-21: a genuinely well-grounded
# answer got an EMPTY sources[] panel in api/main.py because none of its
# citations were recognized. Since we assigned that numbering ourselves,
# N maps directly to chunks[N-1] — recovering the real citation here fixes
# the actual data, not just hides the malformed text (consumer_view.py's
# _SOURCE_LABEL_CITATION_RE only does the latter, for the same root cause).
_SOURCE_LABEL_RE = re.compile(r"^source\s+(\d+)\b", re.IGNORECASE)


def _extract_citations(block_text: str, chunks: list[dict] | None = None) -> list[tuple[str, str]]:
    citations = []
    for group in CITATION_GROUP_RE.findall(block_text):
        for part in group.split(";"):
            part = part.strip()
            m = CITATION_PART_RE.match(part)
            if m:
                citations.append((m.group(1).strip(), m.group(2).strip()))
                continue
            src_m = _SOURCE_LABEL_RE.match(part)
            if src_m and chunks is not None:
                idx = int(src_m.group(1)) - 1
                if 0 <= idx < len(chunks):
                    citations.append((chunks[idx]["source_file"], chunks[idx]["heading"]))
    return citations


# Strips an accidental "Source N: " prefix that a generation model can glue
# onto the filename half of a citation (confirmed real, not hypothetical —
# the model echoed the "[Source 2: ...]" context label's own "Source 2:"
# part into its citation). The prompt-level
# fix (llm.py's SYSTEM_PROMPT) addresses the cause; this is a cheap,
# defense-in-depth normalization so a future model-level regression of the
# same shape degrades gracefully (a match instead of a silent skip) rather
# than needing another citation-format-drift investigation from scratch.
_SOURCE_PREFIX_RE = re.compile(r"^source\s*\d+\s*:\s*", re.IGNORECASE)


def _normalize_for_match(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower()


def _match_chunks(citations: list[tuple[str, str]], chunks: list[dict]) -> list[dict]:
    """
    Matches (source_file, ref) citations against real chunks. Comparison is
    whitespace/case-normalized rather than byte-exact — a citation that
    reproduces a heading's real content but differs only in spacing, case,
    or a trailing/leading annotation should still resolve, rather than
    silently failing open the way Findings 17/18 (an irregular heading) and
    Finding 19 (a "Source N:" prefix) each did under strict `==` equality.

    A ref is also accepted as a match if it's a normalized PREFIX of the
    real heading, cut on a non-alphanumeric boundary — e.g. citing "Chunk 37"
    for a heading of "Chunk 37 — Non-Sugar Sweetener Limits..." matches, but
    "Chunk 5" does NOT falsely match a heading of "Chunk 50 — ..." (the next
    heading character after the prefix, "0", is alphanumeric, so the
    boundary check rejects it). This only ever adds matches on top of the
    original exact-match behavior — it never rejects a citation the old
    logic would have matched — so it's safe for other code that reuses
    this function directly (e.g. eval/faithfulness_score.py's scoring):
    previously-passing cases keep passing, previously-missed cases
    (irregular headings, minor format drift) now can too.
    """
    matched = []
    for source_file, ref in citations:
        clean_source = _SOURCE_PREFIX_RE.sub("", source_file).strip()
        norm_ref = _normalize_for_match(ref)
        for c in chunks:
            if c.get("source_file") != clean_source:
                continue
            norm_heading = _normalize_for_match(c.get("heading", ""))
            if norm_heading == norm_ref:
                matched.append(c)
                break
            if norm_heading.startswith(norm_ref) and (
                len(norm_heading) == len(norm_ref) or not norm_heading[len(norm_ref)].isalnum()
            ):
                matched.append(c)
                break
    return matched


def _numeric_tokens(text: str) -> set[str]:
    # Strip whitespace AND commas so "3 500 ppm" / "3,500 ppm" / "3500 ppm"
    # all normalize to the same token — see _NUMERIC_TOKEN_RE's comment.
    return {re.sub(r"[\s,]+", "", t.lower()) for t in _NUMERIC_TOKEN_RE.findall(text)}


def check_groundedness(answer: str, chunks: list[dict]) -> str:
    blocks = _split_claims(answer)

    out_parts = []
    for tag, block_text in blocks:
        if tag not in CHECKED_TAGS:
            out_parts.append(block_text)
            continue

        citations = _extract_citations(block_text, chunks=chunks)
        if not citations:
            out_parts.append(block_text)
            continue

        matched_chunks = _match_chunks(citations, chunks)
        if not matched_chunks:
            out_parts.append(block_text)
            continue

        hypothesis = TAG_RE.sub("", block_text)
        hypothesis = CITATION_GROUP_RE.sub("", hypothesis).strip()

        hyp_numbers = _numeric_tokens(hypothesis)
        if not hyp_numbers:
            out_parts.append(block_text)
            continue

        premise_text = " ".join(c["text"] for c in matched_chunks)
        if hyp_numbers & _numeric_tokens(premise_text):
            out_parts.append(block_text)
        else:
            out_parts.append(block_text.rstrip() + UNVERIFIED_MARKER)

    return "".join(out_parts)
