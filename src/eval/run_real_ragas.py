"""
eval/run_real_ragas.py — runs the ACTUAL `ragas` PyPI package (not the
hand-rolled equivalent in eval/ragas_metrics.py/run_ragas_eval.py) against
ask_langchain_hybrid.py, computing the same four metrics via ragas's own
implementation: faithfulness, answer relevancy, context precision, context
recall.

Why this exists alongside the hand-rolled harness, not instead of it: see
ARCHITECTURE.md §8 for the original reasoning (a dependency conflict with
this project's now-retired non-LangChain comparison pipelines, and a
concern about eval calls bypassing generation/gateway.py's quota
management). Neither reason blocks a one-off, deliberately-costed run of
the real library against this LangChain-only repo — this script is exactly
that: a real second opinion from the actual, community-maintained metric
implementations, not a replacement for the hand-rolled harness (which stays
the one wired into the gateway's budget ledger for routine runs).

Real, load-bearing bugs found getting the installed ragas==0.4.3 to run at
all, worth recording since they'll bite the next person too:

1. ragas unconditionally imports `langchain_community.chat_models.vertexai.
   ChatVertexAI` at module load, regardless of which provider you actually
   use. The installed langchain-community (0.4.2, mid-"sunset" refactor
   toward lazy submodule loading) has fully removed ChatVertexAI from its
   lazy-loading registry — the file still exists on disk but isn't
   reachable via any import path anymore. Fixed with a tiny import shim
   (below) that registers a dummy module at that exact dotted path before
   `ragas` is imported — we never use Vertex AI, so a stub is harmless.
2. ragas's `llm_factory(provider="groq", client=<groq.Groq instance>)`
   path is itself broken: `_patch_client_for_provider`'s generic branch
   hardcodes an Anthropic-shaped call (`client.messages.create`) for
   EVERY provider that isn't openai/anthropic/google, including groq —
   even though it correctly maps "groq" to `instructor.Provider.GROQ`.
   Since Groq's API is actually OpenAI-compatible, the fix is to route
   through ragas's `provider="openai"` path instead (which correctly uses
   `instructor.from_openai`), passing a real `openai.AsyncOpenAI` client
   pointed at Groq's OpenAI-compatible endpoint
   (`https://api.groq.com/openai/v1`) — instructor's OpenAI adapter does a
   strict `isinstance` check, so a `groq.Groq`/`groq.AsyncGroq` instance
   itself is rejected outright, a genuine `openai.AsyncOpenAI` is required.
3. The installed `instructor` version ragas pulled in (1.3.2) predates
   `instructor.Provider.GENAI`, which ragas's own provider-map dict
   literal references unconditionally at call time (even down the openai
   branch, since Python evaluates the whole dict) — upgraded to the latest
   instructor release to get a version that actually has it.

Run:
    python src/eval/run_real_ragas.py --out ragas_real_report.md
    python src/eval/run_real_ragas.py --n 3                       # cheap pilot
    python src/eval/run_real_ragas.py --questions q01 q08 q27
"""
import argparse
import asyncio
import os
import sys
import types
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()


def _shim_vertexai() -> None:
    """See module docstring, bug 1. Must run before `import ragas`."""
    dotted = "langchain_community.chat_models.vertexai"
    if dotted in sys.modules:
        return
    mod = types.ModuleType(dotted)
    mod.ChatVertexAI = type("ChatVertexAI", (), {})
    sys.modules[dotted] = mod


_shim_vertexai()

from openai import AsyncOpenAI
from ragas.embeddings import HuggingFaceEmbeddings
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)

from ask_langchain_hybrid import ask, build_resources, GROQ_MODEL
from config import EMBEDDING_MODEL
from eval.test_questions import QUESTIONS

GROQ_OPENAI_BASE_URL = "https://api.groq.com/openai/v1"


def _load_groq_keys() -> list[str]:
    """
    Same GROQ_API_KEY/GROQ_API_KEY_2/... convention generation/gateway.py's
    own _load_groq_api_keys() uses.
    """
    keys = []
    primary = os.environ.get("GROQ_API_KEY")
    if primary:
        keys.append(primary)
    i = 2
    while True:
        k = os.environ.get(f"GROQ_API_KEY_{i}")
        if not k:
            break
        keys.append(k)
        i += 1
    if not keys:
        raise SystemExit("No GROQ_API_KEY(_N) set — required for the real ragas judge calls.")
    return keys


def _build_ragas_llms() -> list:
    """
    One ragas LLM instance per configured Groq key, not just the first one.

    Real bug found live 2026-08-26 running the full 20-question batch: a
    single key hit Groq's DAILY token quota (200,000 TPD) partway through
    (cumulative usage from earlier live testing that same day, not from
    this run alone) and every remaining question failed outright — a
    short retry/backoff (see _ascore_with_retry) is useless against a
    DAILY limit, it only helps a transient per-minute one. This project's
    main pipeline (generation/gateway.py, ask_langchain_hybrid.py's own
    groq_gateway_invoke()) already solves exactly this by rotating across
    every configured key; the ragas judge just wasn't doing the same thing.
    """
    llms = []
    for key in _load_groq_keys():
        client = AsyncOpenAI(api_key=key, base_url=GROQ_OPENAI_BASE_URL)
        # ragas's InstructorModelArgs defaults max_tokens=1024 — too small
        # for faithfulness's statement-extraction step on a longer answer
        # (hit IncompleteOutputException live on q02's structured-output
        # call). llm_factory(**kwargs) merges into model_args, overriding
        # the default.
        llms.append(llm_factory(GROQ_MODEL, provider="openai", client=client, max_tokens=4096))
    return llms


RAGAS_CALL_PAUSE_SECONDS = 6  # between metric calls, see comment below
RAGAS_RETRY_BACKOFF_SECONDS = 20  # once every key has been tried once and all failed
RAGAS_MAX_LAPS = 2  # full passes over every key before giving up on this call

_ragas_key_cursor = 0  # mirrors generation/gateway.py's own module-level cursor


def _is_rate_limit_error(e: Exception) -> bool:
    return "429" in str(e) or "rate_limit" in str(e).lower()


async def _ascore_rotating(metric_cls, metric_kwargs: dict, score_kwargs: dict, llms: list):
    """
    Builds a fresh metric instance per attempt (ragas metric objects are
    cheap, just bind an llm) and rotates across every configured Groq key
    on a rate-limit error, same key-rotation shape
    generation/gateway.py::_groq_create() already uses for the main
    pipeline. Only after a FULL lap across every key still fails does this
    fall back to a longer sleep-and-retry lap — see _build_ragas_llms()'s
    docstring for why rotation, not just backoff, is the real fix (a daily
    per-key quota, not a transient per-minute one, is what was actually
    exhausted on the live run that found this gap).
    """
    global _ragas_key_cursor
    last_exc = None
    for lap in range(RAGAS_MAX_LAPS):
        for offset in range(len(llms)):
            idx = (_ragas_key_cursor + offset) % len(llms)
            metric = metric_cls(llm=llms[idx], **metric_kwargs)
            try:
                result = await metric.ascore(**score_kwargs)
                _ragas_key_cursor = idx
                return result
            except Exception as e:
                last_exc = e
                if not _is_rate_limit_error(e):
                    raise
                print(f"    key #{idx + 1}/{len(llms)} rate-limited, trying next key...")
        if lap < RAGAS_MAX_LAPS - 1:
            print(f"    every key rate-limited this lap — backing off {RAGAS_RETRY_BACKOFF_SECONDS}s before retrying...")
            await asyncio.sleep(RAGAS_RETRY_BACKOFF_SECONDS)
    raise last_exc


async def _score_question(q: dict, resources: dict, llms: list, embeddings) -> dict:
    query = q["query"]
    reference = q["reference_answer"]

    answer, chunks = ask(query, verbose=False, resources=resources, return_chunks=True)

    if not chunks:
        return {"id": q["id"], "query": query, "skipped": "no chunks retrieved (structured-only or insufficient-evidence route)"}

    contexts = [f"{c['heading']}: {c['text']}" for c in chunks]

    # Sequential, not asyncio.gather — Groq's per-minute TOKEN rate limit
    # (8000 TPM on this tier, independent of the daily-quota ledger
    # generation/gateway.py tracks) is real and was hit immediately running
    # all 4 metrics concurrently per question. A pause between calls keeps
    # this comfortably under that cap; this is a one-off eval run, not
    # latency-sensitive production traffic, so there's no cost to pacing it.
    faith_r = await _ascore_rotating(
        Faithfulness, {},
        {"user_input": query, "response": answer, "retrieved_contexts": contexts}, llms)
    await asyncio.sleep(RAGAS_CALL_PAUSE_SECONDS)
    rel_r = await _ascore_rotating(
        AnswerRelevancy, {"embeddings": embeddings},
        {"user_input": query, "response": answer}, llms)
    await asyncio.sleep(RAGAS_CALL_PAUSE_SECONDS)
    prec_r = await _ascore_rotating(
        ContextPrecision, {},
        {"user_input": query, "reference": reference, "retrieved_contexts": contexts}, llms)
    await asyncio.sleep(RAGAS_CALL_PAUSE_SECONDS)
    rec_r = await _ascore_rotating(
        ContextRecall, {},
        {"user_input": query, "retrieved_contexts": contexts, "reference": reference}, llms)

    return {
        "id": q["id"],
        "query": query,
        "faithfulness": faith_r.value,
        "answer_relevancy": rel_r.value,
        "context_precision": prec_r.value,
        "context_recall": rec_r.value,
    }


async def run(question_ids: list[str] | None, n: int | None, out_path: str) -> None:
    eligible = [q for q in QUESTIONS if q.get("reference_answer")]
    if question_ids:
        wanted = set(question_ids)
        eligible = [q for q in eligible if q["id"] in wanted]
    if n:
        eligible = eligible[:n]

    print(f"Running real ragas against {len(eligible)} question(s): {[q['id'] for q in eligible]}")

    print("Loading pipeline resources (embedding model, Qdrant client, BM25 index, cross-encoder)...")
    resources = build_resources()

    llms = _build_ragas_llms()
    print(f"Building ragas judge (Groq model {GROQ_MODEL} via OpenAI-compatible endpoint, "
          f"{len(llms)} key(s) configured for rotation)...")
    embeddings = HuggingFaceEmbeddings(model=EMBEDDING_MODEL)

    results = []
    for q in eligible:
        print(f"\n[{q['id']}] {q['query']}")
        try:
            result = await _score_question(q, resources, llms, embeddings)
        except Exception as e:
            # A single question's real, non-rate-limit failure (already
            # retried by _ascore_with_retry for the transient case) must
            # not lose every other already-scored question — confirmed
            # real: an earlier run crashed uncaught on question 6 of 20 and
            # the report was never written at all, losing 5 good results.
            print(f"  ERROR — {e}")
            result = {"id": q["id"], "query": q["query"], "skipped": f"error: {e}"}
        if "skipped" in result:
            print(f"  SKIPPED — {result['skipped']}")
        else:
            print(f"  faithfulness={result['faithfulness']:.3f}  answer_relevancy={result['answer_relevancy']:.3f}  "
                  f"context_precision={result['context_precision']:.3f}  context_recall={result['context_recall']:.3f}")
        results.append(result)
        # Written after every question, not just at the end -- see the
        # comment above on why losing partial progress on a crash is a real
        # problem this had, not a hypothetical one.
        _write_report(results, out_path)
    print(f"\nReport written to {out_path}")


def _mean(results: list[dict], key: str) -> float | None:
    values = [r[key] for r in results if key in r and r[key] is not None]
    return sum(values) / len(values) if values else None


def _write_report(results: list[dict], out_path: str) -> None:
    scored = [r for r in results if "skipped" not in r]
    skipped = [r for r in results if "skipped" in r]

    lines = [
        "# Real RAGAS evaluation report",
        "",
        f"Real `ragas` PyPI package (not the hand-rolled equivalent) against `ask_langchain_hybrid.py`. "
        f"{len(scored)} question(s) scored, {len(skipped)} skipped.",
        "",
        "## Summary",
        "",
        "| Metric | Mean |",
        "|---|---|",
        f"| Faithfulness | {_mean(scored, 'faithfulness'):.3f} |" if _mean(scored, "faithfulness") is not None else "| Faithfulness | n/a |",
        f"| Answer Relevancy | {_mean(scored, 'answer_relevancy'):.3f} |" if _mean(scored, "answer_relevancy") is not None else "| Answer Relevancy | n/a |",
        f"| Context Precision | {_mean(scored, 'context_precision'):.3f} |" if _mean(scored, "context_precision") is not None else "| Context Precision | n/a |",
        f"| Context Recall | {_mean(scored, 'context_recall'):.3f} |" if _mean(scored, "context_recall") is not None else "| Context Recall | n/a |",
        "",
        "## Per-question",
        "",
        "| ID | Query | Faithfulness | Answer Relevancy | Context Precision | Context Recall |",
        "|---|---|---|---|---|---|",
    ]
    for r in scored:
        lines.append(
            f"| {r['id']} | {r['query']} | {r['faithfulness']:.3f} | {r['answer_relevancy']:.3f} | "
            f"{r['context_precision']:.3f} | {r['context_recall']:.3f} |"
        )
    if skipped:
        lines += ["", "## Skipped", ""]
        for r in skipped:
            lines.append(f"- **{r['id']}** ({r['query']}): {r['skipped']}")

    Path(out_path).write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default="ragas_real_report.md")
    parser.add_argument("--n", type=int, default=None, help="Limit to the first N eligible questions.")
    parser.add_argument("--questions", nargs="+", default=None, help="Specific question ids, e.g. q01 q08 q27.")
    args = parser.parse_args()

    asyncio.run(run(args.questions, args.n, args.out))
