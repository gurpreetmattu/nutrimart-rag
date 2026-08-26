"""
eval/ragas_metrics.py — hand-rolled RAGAS-equivalent metrics (faithfulness,
answer relevancy, context precision, context recall), scoped 2026-08-24 and
implemented here rather than installing the real `ragas` pip package.

Why hand-rolled, not the real package: `ragas` calls its judge LLM through
LangChain's own wrapper abstractions. This project's two original pipelines
(`ask.py`, `ask_hybrid.py`) are deliberately plain-Python controls with no
framework — and even for the LangChain pipeline this evaluates
(`ask_langchain_hybrid.py`), wiring `ragas` in would mean its judge calls
bypass this project's own quota management (`generation/gateway.py`'s
multi-key rotation, `generation/token_budget.py`'s proactive per-key daily
ledger) and hit Groq directly, uncoordinated with every other call this app
makes. Every judge call here instead goes through
`generation/gateway.py::complete()` — same multi-key rotation, same
proactive budget check, same HF fallback, same usage tracking, for free.

Same technique RAGAS itself uses (decompose an answer into atomic claims,
then LLM-verify each claim against context) — just without the LangChain
dependency chain. One real, disclosed simplification from RAGAS's own
default behavior: context precision here is ONE batched judge call across
all retrieved chunks (unweighted precision — fraction judged relevant),
not RAGAS's default of one call per chunk with rank-weighting. That's a
deliberate cost-control choice (this project's chunks run 300-800+ tokens
each; one call per chunk would roughly double this metric's own cost) —
disclosed here, not silently cut.

Every function takes real pipeline output (`chunks` in the exact dict shape
`ask_hybrid.py`/`ask_langchain_hybrid.py` retrieval returns —
`source_file`/`heading`/`text`/`rerank_score`) and returns a dict with a
`score` (float 0-1, or None if nothing could be scored) plus the raw
judge output for manual inspection — scores alone hide WHY something
scored low, same reasoning `groundedness.py`'s inline markers already use.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import BGE_QUERY_PREFIX
from generation.gateway import complete
from generation.llm import build_context_block, GENERATION_REASONING_EFFORT

_NUMBERED_LINE_RE = re.compile(r"^\s*(\d+)[\.\):]\s*(.+?)\s*$")
_YES_NO_RE = re.compile(r"\b(yes|no)\b", re.IGNORECASE)

_DECOMPOSE_SYSTEM_PROMPT = """Break the given text into a list of atomic, standalone factual claims. \
Each claim must be understandable on its own, without needing any other claim for context — resolve \
pronouns and implicit references. Do not add, omit, or change any factual content. Output ONLY a \
numbered list, one claim per line, no preamble, no explanation."""

_VERIFY_SYSTEM_PROMPT = """You will be given a numbered list of claims and a context. For each claim, \
decide whether it can be directly inferred from the context alone — respond YES only if the context \
actually supports the claim, NO otherwise (including when the context is silent on it). Output ONLY \
one line per claim in the exact format "N. YES" or "N. NO", no explanations, no other text."""


def _parse_numbered_list(text: str) -> list[str]:
    items = []
    for line in text.strip().splitlines():
        m = _NUMBERED_LINE_RE.match(line)
        if m:
            items.append(m.group(2).strip())
    return items


def _parse_yes_no(text: str, n: int) -> list[bool | None]:
    """
    Returns a list of length n (True/False/None per claim index, None if
    that line couldn't be parsed at all) — never silently drops a claim,
    since a missing verdict changing the denominator would quietly inflate
    a score. Tolerant of a stray "N." with the YES/NO elsewhere on the
    line (real observed LLM output shape), not just the exact "N. YES".
    """
    verdicts: list[bool | None] = [None] * n
    for line in text.strip().splitlines():
        m = _NUMBERED_LINE_RE.match(line)
        if not m:
            continue
        idx_str, rest = m.group(1), m.group(2)
        try:
            idx = int(idx_str) - 1
        except ValueError:
            continue
        if not (0 <= idx < n):
            continue
        yn = _YES_NO_RE.search(rest)
        if yn:
            verdicts[idx] = yn.group(1).lower() == "yes"
    return verdicts


def _score_from_verdicts(verdicts: list[bool | None]) -> tuple[float | None, int, int]:
    """Returns (score, n_true, n_parsed) — score is None if nothing parsed at all."""
    parsed = [v for v in verdicts if v is not None]
    if not parsed:
        return None, 0, 0
    n_true = sum(1 for v in parsed if v)
    return n_true / len(parsed), n_true, len(parsed)


def faithfulness(
    question: str, answer: str, chunks: list[dict], usage_out: list | None = None,
    known_facts_block: str | None = None,
) -> dict:
    """
    Does the answer avoid claiming things the retrieved context doesn't
    support? Two calls: decompose the answer into atomic claims, then one
    batched call verifying every claim against the same context block the
    generator actually saw (`build_context_block`, not a re-derived copy).

    `known_facts_block` (added 2026-08-25, real bug found via q05/q07's
    low scores): `generate_answer_lc()`'s own prompt legitimately grounds
    some claims in `known_facts` (products.sqlite nutrition/ingredient
    data, e.g. "8.3mg sodium (products.sqlite)") woven inline into the
    KB-grounded answer — not just the leading structured-tool prefix
    `run_ragas_eval.py` already strips. Those claims are real and
    correctly sourced, just not from a KB chunk, so without this they get
    judged NO purely because the judge's context is chunks-only. Confirmed
    via live diagnosis: q05's "[FACT] Diet Coke lists aspartame (INS 951)
    ... (products.sqlite, diet_coke)" and q07's compound INTERPRETATION
    claim bundling several products.sqlite nutrition values both scored as
    unsupported for exactly this reason. Passing the SAME known_facts
    block the generator saw (`build_known_facts_block`) as extra judge
    context closes the gap without weakening what still counts as a real
    hallucination — a claim citing neither a chunk nor a known fact still
    correctly scores NO.
    """
    if not answer.strip():
        return {"score": None, "claims": [], "verdicts": [], "note": "empty answer, nothing to check"}

    decompose_response = complete(
        _DECOMPOSE_SYSTEM_PROMPT, answer, max_tokens=900,
        call_name="ragas_faithfulness_decompose", usage_out=usage_out,
        reasoning_effort=GENERATION_REASONING_EFFORT,
    )
    claims = _parse_numbered_list(decompose_response)
    if not claims:
        return {"score": None, "claims": [], "verdicts": [], "note": "no claims extracted"}

    context_block = build_context_block(chunks)
    if known_facts_block:
        context_block = f"{context_block}\n\n---\n\nKnown product facts (products.sqlite):\n{known_facts_block}"
    claims_block = "\n".join(f"{i}. {c}" for i, c in enumerate(claims, 1))
    verify_response = complete(
        _VERIFY_SYSTEM_PROMPT, f"Claims:\n{claims_block}\n\n---\n\nContext:\n{context_block}",
        max_tokens=700, call_name="ragas_faithfulness_verify", usage_out=usage_out,
        reasoning_effort=GENERATION_REASONING_EFFORT,
    )
    verdicts = _parse_yes_no(verify_response, len(claims))
    score, n_true, n_parsed = _score_from_verdicts(verdicts)
    return {
        "score": score, "claims": claims, "verdicts": verdicts,
        "note": f"{n_true}/{n_parsed} claims supported" + (
            f" ({len(claims) - n_parsed} unparsed)" if n_parsed < len(claims) else ""
        ),
    }


_RELEVANCY_SYSTEM_PROMPT = """Given an answer, generate exactly 3 different questions that this answer \
would be a good, direct response to. Vary the phrasing across the 3. Output ONLY a numbered list of 3 \
questions, no preamble, no explanation."""


def answer_relevancy(question: str, answer: str, embed_fn, usage_out: list | None = None) -> dict:
    """
    Does the answer actually address the question (vs. being vague,
    padded, or off-topic)? Generates 3 paraphrased questions the answer
    could be responding to, embeds them plus the real question with
    `embed_fn` (pass the already-loaded bge model's `.encode`, e.g.
    `resources["dense_model"].encode` — no extra LLM cost for this half of
    the metric, unlike RAGAS's own default which re-embeds through
    whatever embedding provider is configured). Both the real and
    generated questions get `BGE_QUERY_PREFIX` — this is a
    question-to-question comparison (symmetric), and bge's query prefix
    convention only matters for consistency between the two sides being
    compared, not for correctness of either side alone; prefixing both the
    same way keeps the comparison apples-to-apples.
    """
    if not answer.strip():
        return {"score": None, "generated_questions": [], "note": "empty answer, nothing to check"}

    response = complete(
        _RELEVANCY_SYSTEM_PROMPT, answer, max_tokens=500,
        call_name="ragas_answer_relevancy", usage_out=usage_out,
        reasoning_effort=GENERATION_REASONING_EFFORT,
    )
    generated = _parse_numbered_list(response)
    if not generated:
        return {"score": None, "generated_questions": [], "note": "no questions generated"}

    import numpy as np

    q_vec = embed_fn([BGE_QUERY_PREFIX + question], normalize_embeddings=True)[0]
    gen_vecs = embed_fn([BGE_QUERY_PREFIX + g for g in generated], normalize_embeddings=True)
    sims = [float(np.dot(q_vec, v)) for v in gen_vecs]
    score = sum(sims) / len(sims)
    return {"score": score, "generated_questions": generated, "similarities": sims}


_PRECISION_SYSTEM_PROMPT = """You will be given a question and a numbered list of context passages. For \
each passage, decide whether it is relevant to answering the question — respond YES if it contains \
information useful for answering, NO if it's off-topic or irrelevant. Output ONLY one line per passage \
in the exact format "N. YES" or "N. NO", no explanations, no other text."""

_PRECISION_CHUNK_CHAR_LIMIT = 600  # relevance judgment doesn't need the full chunk text, see module docstring


def context_precision(question: str, chunks: list[dict], usage_out: list | None = None) -> dict:
    """
    Of the retrieved chunks, how many were actually relevant to the
    question? Simplified, unweighted precision (fraction judged relevant),
    not RAGAS's default rank-weighted version — see module docstring.
    """
    if not chunks:
        return {"score": None, "verdicts": [], "note": "no retrieved chunks"}

    passages_block = "\n\n".join(
        f"[{i}] {c['source_file']}, {c['heading']}\n{c['text'][:_PRECISION_CHUNK_CHAR_LIMIT]}"
        for i, c in enumerate(chunks, 1)
    )
    response = complete(
        _PRECISION_SYSTEM_PROMPT, f"Question: {question}\n\nPassages:\n{passages_block}",
        max_tokens=500, call_name="ragas_context_precision", usage_out=usage_out,
        reasoning_effort=GENERATION_REASONING_EFFORT,
    )
    verdicts = _parse_yes_no(response, len(chunks))
    score, n_true, n_parsed = _score_from_verdicts(verdicts)
    return {
        "score": score, "verdicts": verdicts,
        "note": f"{n_true}/{n_parsed} chunks relevant" + (
            f" ({len(chunks) - n_parsed} unparsed)" if n_parsed < len(chunks) else ""
        ),
    }


def context_recall(reference_answer: str, chunks: list[dict], usage_out: list | None = None) -> dict:
    """
    Did retrieval surface everything needed to answer correctly? Same
    decompose-then-verify technique as faithfulness, but applied to the
    ground-truth `reference_answer` (from `test_questions.py`) instead of
    the model's own generated answer, checked against the SAME retrieved
    context — a low score here means retrieval missed something a correct
    answer needs, independent of whether the model's own answer was good.
    """
    if not reference_answer.strip():
        return {"score": None, "claims": [], "verdicts": [], "note": "no reference answer given"}
    if not chunks:
        return {"score": None, "claims": [], "verdicts": [], "note": "no retrieved chunks"}

    decompose_response = complete(
        _DECOMPOSE_SYSTEM_PROMPT, reference_answer, max_tokens=700,
        call_name="ragas_context_recall_decompose", usage_out=usage_out,
        reasoning_effort=GENERATION_REASONING_EFFORT,
    )
    claims = _parse_numbered_list(decompose_response)
    if not claims:
        return {"score": None, "claims": [], "verdicts": [], "note": "no claims extracted"}

    context_block = build_context_block(chunks)
    claims_block = "\n".join(f"{i}. {c}" for i, c in enumerate(claims, 1))
    verify_response = complete(
        _VERIFY_SYSTEM_PROMPT, f"Claims:\n{claims_block}\n\n---\n\nContext:\n{context_block}",
        max_tokens=700, call_name="ragas_context_recall_verify", usage_out=usage_out,
        reasoning_effort=GENERATION_REASONING_EFFORT,
    )
    verdicts = _parse_yes_no(verify_response, len(claims))
    score, n_true, n_parsed = _score_from_verdicts(verdicts)
    return {
        "score": score, "claims": claims, "verdicts": verdicts,
        "note": f"{n_true}/{n_parsed} reference claims covered by retrieval" + (
            f" ({len(claims) - n_parsed} unparsed)" if n_parsed < len(claims) else ""
        ),
    }
