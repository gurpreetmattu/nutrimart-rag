"""
eval/run_ragas_eval.py — runs the RAGAS-equivalent metrics
(eval/ragas_metrics.py) against `ask_langchain_hybrid.py` specifically, not
`ask_hybrid.py` or `ask.py` (explicit user request, 2026-08-24) — writes a
markdown report, same convention as benchmark_pipeline.py/
run_phase7_comparison.py.

Only runs the 20 RAG-eligible questions (q01-q10, q21-q30) — see
test_questions.py's 2026-08-24 module docstring note for why q12-q20 are
excluded (they hit the deterministic product_fact SQL route and never
touch retrieval/generation, so a RAG metric has nothing to measure).

A question whose real routing decision doesn't produce retrieved chunks
(e.g. it happens to resolve to a structured-tools-only answer, or hits
insufficient-evidence) is reported but not scored on the context-based
metrics (context precision/recall need real retrieved chunks; faithfulness
needs them too since it verifies against context) — this is REAL pipeline
behavior surfacing, not a bug in this script, and it's reported honestly
as "skipped" rather than silently omitted or scored as 0.

Usage:
    python src/eval/run_ragas_eval.py                       # all 20 questions
    python src/eval/run_ragas_eval.py --n 3                  # cheap pilot
    python src/eval/run_ragas_eval.py --questions q22 q23    # specific ids
    python src/eval/run_ragas_eval.py --out ragas_report.md
"""
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv
load_dotenv()

from eval.test_questions import QUESTIONS
from eval.ragas_metrics import faithfulness, answer_relevancy, context_precision, context_recall
from generation.llm import build_known_facts_block

RAG_ELIGIBLE_IDS = [f"q{i:02d}" for i in range(1, 11)] + [f"q{i}" for i in range(21, 31)]

DELAY_BETWEEN_QUESTIONS_SEC = 1.5


def _stats(values: list[float]) -> dict:
    values = [v for v in values if v is not None]
    if not values:
        return {"mean": None, "n": 0}
    return {"mean": sum(values) / len(values), "n": len(values)}


def run_all(question_ids: list[str]) -> tuple[str, list[dict]]:
    from api.resources import get_resources
    from ask_langchain_hybrid import ask

    print("Loading pipeline resources once (not measured as per-query cost)...")
    resources = get_resources()

    questions = [q for q in QUESTIONS if q["id"] in question_ids]
    print(f"Running RAGAS-equivalent metrics for {len(questions)} questions "
          f"against ask_langchain_hybrid.py...\n")

    rows = []
    for i, q in enumerate(questions, 1):
        print(f"[{i}/{len(questions)}] {q['id']}: {q['query']!r}")
        row = {"id": q["id"], "query": q["query"]}
        usage: list = []
        try:
            answer, chunks, structured_answers, known_facts = ask(
                q["query"], resources=resources, verbose=False,
                return_chunks=True, return_structured_answers=True,
                return_known_facts=True, usage=usage,
            )
            row["answer"] = answer
            row["usage"] = usage

            # Faithfulness checks claims against the retrieved KB `chunks`
            # PLUS known_facts (products.sqlite data merged into the
            # generation prompt, see faithfulness()'s known_facts_block
            # param, added 2026-08-25 after q05/q07 both scored low purely
            # because a SQL-grounded claim woven inline had nothing to match
            # in chunks-only context). A structured tool's own output
            # (prepended to `answer`, e.g. from lookup_product_fact/
            # check_ingredient_or_allergen) is separately, deterministically
            # grounded in products.sqlite and was never meant to be
            # re-verified against KB context at all (check_groundedness()
            # itself only checks the generated portion, same precedent) —
            # strip that known prefix before decomposing.
            generation_only_answer = answer
            if structured_answers:
                prefix = "\n\n".join(structured_answers) + "\n\n"
                if answer.startswith(prefix):
                    generation_only_answer = answer[len(prefix):]

            if not chunks:
                row["skipped"] = True
                row["skip_reason"] = "no retrieved chunks (structured-only answer or insufficient-evidence)"
                print(f"    skipped — {row['skip_reason']}")
            else:
                row["skipped"] = False
                known_facts_block = build_known_facts_block(known_facts) if known_facts else None
                row["faithfulness"] = faithfulness(
                    q["query"], generation_only_answer, chunks, usage_out=usage,
                    known_facts_block=known_facts_block,
                )
                row["answer_relevancy"] = answer_relevancy(
                    q["query"], answer, resources["dense_model"].encode, usage_out=usage,
                )
                row["context_precision"] = context_precision(q["query"], chunks, usage_out=usage)
                row["context_recall"] = context_recall(
                    q.get("reference_answer", ""), chunks, usage_out=usage,
                )
                print(f"    faithfulness={row['faithfulness']['score']}, "
                      f"answer_relevancy={row['answer_relevancy']['score']}, "
                      f"context_precision={row['context_precision']['score']}, "
                      f"context_recall={row['context_recall']['score']}")
        except Exception as e:
            row["error"] = str(e)
            print(f"    ERROR: {e}")

        rows.append(row)
        if i < len(questions):
            time.sleep(DELAY_BETWEEN_QUESTIONS_SEC)

    return _render_report(rows), rows


def _render_report(rows: list[dict]) -> str:
    lines = [
        f"# RAGAS-equivalent Evaluation — ask_langchain_hybrid.py — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Hand-rolled faithfulness/answer-relevancy/context-precision/context-recall metrics "
        "(see `eval/ragas_metrics.py`'s module docstring for why hand-rolled instead of the real "
        "`ragas` package, and the one disclosed simplification vs. its defaults: context precision "
        "is one batched judge call, not one call per chunk). Run against `ask_langchain_hybrid.py` "
        "specifically, not `ask_hybrid.py` or `ask.py` — explicit scope for this run.",
        "",
        "## Per-question scores",
        "",
        "| id | faithfulness | answer_relevancy | context_precision | context_recall | note |",
        "|---|---|---|---|---|---|",
    ]

    for row in rows:
        if "error" in row:
            lines.append(f"| {row['id']} | ERROR | ERROR | ERROR | ERROR | {row['error']} |")
            continue
        if row.get("skipped"):
            lines.append(f"| {row['id']} | — | — | — | — | skipped: {row['skip_reason']} |")
            continue
        f_score = row["faithfulness"]["score"]
        r_score = row["answer_relevancy"]["score"]
        p_score = row["context_precision"]["score"]
        c_score = row["context_recall"]["score"]

        def fmt(s):
            return f"{s:.2f}" if s is not None else "n/a"

        note = row["faithfulness"].get("note", "")
        lines.append(f"| {row['id']} | {fmt(f_score)} | {fmt(r_score)} | {fmt(p_score)} | {fmt(c_score)} | {note} |")

    lines += ["", "## Aggregate scores", "", "| metric | mean | n scored |", "|---|---|---|"]
    for metric_key, label in [
        ("faithfulness", "Faithfulness"), ("answer_relevancy", "Answer relevancy"),
        ("context_precision", "Context precision"), ("context_recall", "Context recall"),
    ]:
        values = [row[metric_key]["score"] for row in rows if not row.get("skipped") and "error" not in row]
        s = _stats(values)
        mean_str = f"{s['mean']:.3f}" if s["mean"] is not None else "n/a"
        lines.append(f"| {label} | {mean_str} | {s['n']} |")

    n_skipped = sum(1 for row in rows if row.get("skipped"))
    n_error = sum(1 for row in rows if "error" in row)
    lines += ["", f"Skipped (no retrieved chunks): {n_skipped}. Errored: {n_error}. "
                  f"Total questions run: {len(rows)}.", ""]

    lines += ["## Token usage (real gateway usage.* fields, all calls including the "
              "pipeline's own generation call and every judge call this eval made)", "",
              "| id | call | provider | prompt_tokens | completion_tokens | reasoning_tokens | total_tokens |",
              "|---|---|---|---|---|---|---|"]
    total_tokens_all = 0
    for row in rows:
        for u in row.get("usage", []):
            lines.append(f"| {row['id']} | {u['call']} | {u.get('provider', '?')} | "
                          f"{u['prompt_tokens']} | {u['completion_tokens']} | "
                          f"{u['reasoning_tokens']} | {u['total_tokens']} |")
            total_tokens_all += u.get("total_tokens", 0) or 0
    lines += ["", f"**Total tokens spent across this entire run: {total_tokens_all}**", ""]

    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=None, help="Sample size from the RAG-eligible question list.")
    parser.add_argument("--questions", nargs="*", default=None, help="Explicit question IDs to run instead.")
    parser.add_argument("--out", default="ragas_report.md", help="Output filename, written to project root.")
    args = parser.parse_args()

    if args.questions:
        ids = args.questions
    elif args.n:
        ids = RAG_ELIGIBLE_IDS[:args.n]
    else:
        ids = RAG_ELIGIBLE_IDS

    report, _rows = run_all(ids)

    out_path = Path(args.out)
    out_path.write_text(report, encoding="utf-8")
    print(f"\nDone. Report written to {out_path.resolve()}")
