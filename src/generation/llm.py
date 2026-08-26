"""
llm.py — turns retrieved chunks + a query into a generated answer.

The actual Groq/Hugging Face API calls live in generation/gateway.py (added
2026-08-19 for automatic fallback when Groq's daily quota is exhausted —
see gateway.py's docstring) — this file owns the prompts and the
typed-claim contract, gateway.py owns which provider actually serves a
given call.

GENERATION_MODEL was originally llama-3.3-70b-versatile; Groq deprecated
that model (and its llama-3.1-8b-instant fallback) sometime between
2026-08-15 and 2026-08-17 — both now 404 with "model does not exist or
you do not have access to it," confirmed directly against
GET /openai/v1/models. Swapped to openai/gpt-oss-120b, currently
available on the same account. Check console.groq.com / the models
endpoint for current rate limits and available models — these change.

Enforces the typed-claim system from project_state_summary.md's pipeline
design: every non-obvious claim in the answer must be tagged
[FACT] / [DERIVED CALCULATION] / [INTERPRETATION] / [REGULATORY] / [UNCERTAIN]
and non-FACT claims must cite which retrieved chunk they came from.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generation.gateway import complete

GENERATION_MODEL = "openai/gpt-oss-120b"  # kept for reference; gateway.py's GROQ_MODEL is the real source of truth

# 'low', not None/'medium' (Groq's default) — real evidence, not a guess,
# though from a smaller sample than ideal (see caveat below). Multiple real
# generate_answer() calls this session (2026-08-19, PHASE3_TESTING_LOG.md
# Finding 19) spent 800-1100+ of ~1300 completion tokens (up to ~85%) on
# hidden reasoning at the default effort. One real call at 'low' on a
# similarly-shaped query spent only 21 reasoning tokens — a roughly 97%
# reduction — while the visible answer stayed fully compliant with
# SYSTEM_PROMPT: correct tag-first ordering, correct (source_file, heading)
# citation format on 3 of its 4 claims, and an appropriate [UNCERTAIN] tag
# on the one genuinely unknown fact. Caveat, stated plainly: this is one
# real 'low' sample verified against real historical 'medium' samples, not
# a clean same-query paired A/B — Groq's daily quota (200,000 TPD) was hit
# exactly mid-comparison before a same-query 'medium' data point could be
# collected. Re-verify with a larger sample if this is ever revisited; the
# direction and magnitude of the effect are real, but the sample is thin.
GENERATION_REASONING_EFFORT: str | None = "low"

SYSTEM_PROMPT = """You are a product-information assistant for a quick-commerce grocery app. \
You answer questions about packaged food products using ONLY the retrieved context provided \
below — you do not use outside knowledge about these specific products, ingredients, or \
regulations, even if you believe you know the answer.

LENGTH — keep the answer SHORT: 4-5 sentences/claims at the absolute most, even when much more \
retrieved context is available. Pick only the most directly decision-useful points for what the \
user actually asked and state them concisely — do not enumerate every retrieved fact, every \
nutrition field, or every tangential regulatory detail just because it's available. If the \
question is narrow (e.g. about one ingredient, one number), answer just that narrow question; \
don't pad it out with the full nutrition panel or the full ingredient list unless the user asked \
for those specifically. This length rule applies even to interpretive/health-assessment answers — \
be concise and direct rather than exhaustive.

NEVER NARRATE YOUR OWN PROCESS — the user never sees "retrieved context," "the retrieved \
information," or any other phrase describing how you produced the answer; to them, you simply \
know or don't know something. Wrong: "The retrieved ingredient information does not list milk, but \
the label data does not confirm its absence either." Correct: "[UNCERTAIN] Whether this product \
contains milk isn't confirmed." When something genuinely isn't known, say so plainly with \
[UNCERTAIN] and state what IS known — never describe the retrieval process itself as the reason.

CLAIM TYPING — every sentence in your answer that isn't a bare restatement of the user's \
question must be tagged with one of these prefixes:
- [FACT] — directly stated in a retrieved chunk with high confidence
- [REGULATORY] — a legal/compliance claim from a retrieved regulatory or claims_advertising chunk
- [INTERPRETATION] — your synthesis or explanation built on top of retrieved facts, not a direct quote
- [DERIVED CALCULATION] — a number you computed from retrieved data (state the calculation)
- [UNCERTAIN] — the retrieved context is incomplete, conflicting, or explicitly flags a gap

The tag ALWAYS goes at the very start of the sentence, immediately before the claim text — never at \
the end of the sentence, never after the citation. Correct: "[FACT] BHA is permitted up to 0.005% \
(fssai_knowledge_base.md, Chunk 4)." Wrong: "BHA is permitted up to 0.005% (fssai_knowledge_base.md, \
Chunk 4). [FACT]" — this ordering is not acceptable, always lead with the tag.

After each tagged claim, cite the source using EXACTLY this format: (source_file.md, exact chunk/entry name), \
e.g. (fssai_knowledge_base.md, Chunk 37) or (ingredient_knowledge_base.md, INS 951 — Aspartame). Each piece of \
context above is prefixed with a label like "[Source 2: fssai_knowledge_base.md, Chunk 37]" — copy ONLY the \
filename and chunk/entry name that come after the colon in that label, and drop the "Source N:" part entirely; \
it is a label for you, not part of the citation. Correct: "(fssai_knowledge_base.md, Chunk 37)". Wrong: \
"(Source 2: fssai_knowledge_base.md, Chunk 37)" or "(Source 2)" — both are unacceptable, the citation must \
contain only the filename and chunk/entry name and nothing else, no "Source" word and no number. Always write \
out the full filename and chunk/entry name in every citation, even if you already cited the same source in a \
previous sentence — never abbreviate, and never use bracket/footnote-style citations like 【Source 1】.

If the retrieved context does not contain enough information to answer confidently, say so \
explicitly using [UNCERTAIN] rather than filling the gap from general knowledge. This matters \
most for additives explicitly marked as "genuine regulatory gap" in the retrieved context — \
never state a specific regulatory limit for these unless the retrieved text actually states one.

EVIDENCE RULES — these prevent five specific reasoning errors this assistant has made before. \
Follow them exactly:

1. An unknown product-specific quantity stays unknown. A regulatory limit for an ingredient \
(e.g. "PGPR permitted up to 5,000 mg/kg") does NOT tell you how much of that ingredient is in \
THIS product. Never turn "the limit is X" into "this product is within X" or "probably below X" \
unless the retrieved context also states the product's actual quantity. Correct: "[UNCERTAIN] I \
can confirm PGPR is permitted up to 5,000 mg/kg, but not whether this product's actual amount is \
below that limit — the label doesn't disclose it." Wrong: "[FACT] PGPR is used well below its \
permitted maximum."

2. Meeting a regulatory requirement is not the same as being healthy. Never write or imply that \
because something is legally compliant, it is therefore a good, safe, or healthy choice. These \
are separate questions — compliance is about the law, healthiness is about nutrition and the \
individual eating it.

3. An ingredient appearing on a product's ingredient list tells you it is present, not how much \
of it is present. Never estimate or assume a quantity from presence alone.

4. Known facts established earlier in this conversation (listed below, if any) are ground truth \
for this exchange. Never contradict them, and never claim a value is "not available" or "not \
specified" if it is listed as a known fact — use that exact value instead.

5. Never invent or estimate a missing nutrition value (calories, sugar, fat, etc.) from what's \
"typical" for that category of food. If a specific product's nutrition data is missing from the \
retrieved context, say so with [UNCERTAIN] rather than substituting a generic estimate.

6. Stay SHORT (see LENGTH above) — 4-5 sentences/claims at the absolute most, covering only the \
most decision-relevant points, not an exhaustive dump of everything retrieved.
"""


REWRITE_SYSTEM_PROMPT = """You rewrite search queries to improve retrieval against a food-regulation \
and ingredient knowledge base. Expand abbreviations, add likely synonyms or related regulatory \
terms, and make implicit subjects explicit. Return ONLY the rewritten query, nothing else — no \
explanation, no quotes.

Your rewritten query MUST be different from the input query — returning the input unchanged (even \
word-for-word identical) defeats the entire purpose of this step and is never an acceptable answer. \
If the query already looks complete, still add explicit regulatory/technical synonyms or expand any \
implicit subject so the output is textually different from the input, e.g. rewrite "can a product say \
low sugar" to something like "Can a product be labeled or advertised as 'low sugar' or 'reduced sugar' \
under FSSAI nutrition claim regulations and thresholds?" — never return "can a product say low sugar" \
as-is."""


def rewrite_query(original_query: str, usage_out: list | None = None) -> str:
    """
    Corrective-retry step (project_state_summary.md pipeline step 5): called
    by ask_hybrid.py when the first retrieval pass's top reranked chunk
    scores below RERANK_SCORE_THRESHOLD. One extra LLM call via gateway.complete()
    (Groq, falling back to Hugging Face on quota exhaustion).
    """
    content = complete(
        REWRITE_SYSTEM_PROMPT, original_query,
        # 400, not 128 — GENERATION_MODEL is a reasoning model that spends a
        # variable, non-deterministic number of hidden reasoning tokens
        # before emitting visible content (confirmed directly: reasoning
        # token counts of 67-126 seen on this exact call, out of a 128
        # budget). At 128 this reasoning alone could exhaust the whole
        # budget, leaving empty/truncated content and masquerading as
        # "the model returned nothing" (see llm.py's fallback below,
        # and PHASE3_TESTING_LOG.md Finding 10 bug #4) when it was really
        # a too-small max_tokens for this model shape.
        max_tokens=400, call_name="rewrite_query",
        reasoning_effort=GENERATION_REASONING_EFFORT, usage_out=usage_out,
    )

    rewritten = content.strip()
    if not rewritten:
        # openai/gpt-oss-120b occasionally returns empty content for this
        # call (confirmed directly, e.g. "can a product say low sugar" —
        # not a rare fluke, reproducible on that exact query). An empty
        # string used as a search query produces near-random low scores
        # rather than a genuine "no better query found" signal, so fall
        # back to the original query — retrieve_hybrid_with_retry's second
        # pass then re-scores the same query, which correctly still lands
        # on insufficient-evidence if nothing was really retrievable,
        # without corrupting the result with a bogus empty-string search.
        return original_query
    return rewritten


def build_context_block(chunks: list[dict]) -> str:
    """Formats retrieved chunks into a numbered context block for the prompt."""
    parts = []
    for i, c in enumerate(chunks, 1):
        parts.append(
            f"[Source {i}: {c['source_file']}, {c['heading']}]\n{c['text']}"
        )
    return "\n\n---\n\n".join(parts)


def build_known_facts_block(known_facts: dict) -> str:
    """
    Formats conversation/state.py's known_facts dict for the prompt, same
    "labeled block, then content" shape build_context_block() already uses
    for retrieved chunks — this is what makes SYSTEM_PROMPT's evidence
    rule 4 actually checkable (problems.md Problem 4: the sugar value
    being "forgotten" a few turns later).
    """
    lines = [f"- {attr} = {fact['value']}{fact['unit']} (from {fact['source']})"
              for attr, fact in known_facts.items()]
    return "\n".join(lines)


def generate_answer(
    query: str, chunks: list[dict], usage_out: list | None = None, known_facts: dict | None = None,
    structured_context: str | None = None,
) -> str:
    context_block = build_context_block(chunks)

    known_facts_section = ""
    if known_facts:
        known_facts_section = (
            f"Known facts established earlier in this conversation:\n"
            f"{build_known_facts_block(known_facts)}\n\n---\n\n"
        )

    # `structured_context`, if given (added 2026-08-21): a structured tool's
    # own already-cited answer from THIS SAME turn (e.g. "may contain
    # milk" from check_ingredient_or_allergen), when ask_hybrid.py's tool
    # loop called both a structured tool AND search_knowledge_base. Without
    # this, generate_answer() only ever saw the retrieved chunks — it had
    # no idea a structured tool had already established a fact this turn,
    # so it would independently (and sometimes wrongly) re-derive or hedge
    # against something already known. Confirmed real: "i am allergen to
    # milk should i buy it?" for a product whose data says "may contain
    # milk" got an interpretive paragraph saying "does not list milk...
    # cannot confirm absence either" — directly contradicting the fact
    # already surfaced in the same answer's first line. Framed the same
    # "ground truth, do not contradict" way known_facts already is (see
    # SYSTEM_PROMPT rule 4).
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

    return complete(
        SYSTEM_PROMPT, user_message,
        # 2048, not 1024 — same reasoning-token-budget issue as
        # rewrite_query() above. Confirmed directly on a real q08-shaped
        # call: at 1024 this model spent as much as 1103 reasoning tokens
        # before any visible content, hitting finish_reason="length" with
        # truncated or fully empty content (root cause of the unexplained
        # q08 discrepancy in PHASE3_TESTING_LOG.md Finding 10 — not a
        # retrieval or routing bug, retrieval was fine at 0.631 rerank).
        max_tokens=2048, call_name="generate_answer",
        reasoning_effort=GENERATION_REASONING_EFFORT, usage_out=usage_out,
    )


if __name__ == "__main__":
    # Quick manual test: python llm.py "<query>"
    # Requires retrieval to already be wired up — see ask.py for the
    # full retrieval + generation flow. This standalone test uses a
    # fake chunk so you can check the prompt/API call works before
    # wiring retrieval in.
    from dotenv import load_dotenv
    load_dotenv()

    query = sys.argv[1] if len(sys.argv) > 1 else "is aspartame safe in Diet Coke"

    fake_chunks = [{
        "source_file": "ingredient_knowledge_base.md",
        "heading": "INS 951 — Aspartame",
        "text": "Used in: Diet Coke. Permitted up to 600 mg/kg. IARC classified it "
                "Group 2B (possibly carcinogenic) in 2023; JECFA reaffirmed the existing "
                "ADI of 40 mg/kg body weight/day the same year. Contraindicated for "
                "people with phenylketonuria (PKU).",
    }]

    print(f"Query: {query}\n{'-'*60}")
    answer = generate_answer(query, fake_chunks)
    print(answer)
