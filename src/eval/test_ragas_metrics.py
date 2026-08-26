"""
eval/test_ragas_metrics.py — regression test for ragas_metrics.py's
known_facts_block fix (Finding 33, 2026-08-25): faithfulness() must include
the SAME known_facts block generate_answer_lc() actually saw in its judge
context, not just the retrieved KB chunks — otherwise a legitimately
products.sqlite-grounded claim woven inline into the answer gets judged
unsupported purely because the judge never saw the data it cited (this was
the real, confirmed root cause of q05/q07's artificially low faithfulness
scores before the fix).

No pytest in this project (see CLAUDE.md) — plain assertions + a __main__
runner, same convention as api/test_security.py and generation/test_token_budget.py.

Monkeypatches eval.ragas_metrics.complete() with a fake that returns
canned, correctly-shaped responses and records exactly what context text
it was called with — makes ZERO real LLM/network calls, same "no cost"
design as the other regression tests in this project.

Run:
    python src/eval/test_ragas_metrics.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import eval.ragas_metrics as rm

_failures: list[str] = []


def check(label: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        _failures.append(label)


# --- fake complete(): records every call, returns canned well-formed output

_calls: list[dict] = []


def _fake_complete(system_prompt, user_message, max_tokens=None, call_name=None, usage_out=None,
                    reasoning_effort=None):
    _calls.append({"system_prompt": system_prompt, "user_message": user_message, "call_name": call_name})
    if call_name == "ragas_faithfulness_decompose":
        return "1. Diet Coke lists aspartame as a declared ingredient.\n2. FSSAI permits aspartame up to 700 ppm."
    if call_name == "ragas_faithfulness_verify":
        return "1. YES\n2. YES"
    raise AssertionError(f"unexpected call_name in this test: {call_name!r}")


_original_complete = rm.complete
rm.complete = _fake_complete

try:
    chunks = [
        {"source_file": "fssai_knowledge_base.md", "heading": "Chunk 50",
         "text": "FSSAI permits aspartame up to 700 ppm in carbonated beverages."},
    ]
    known_facts_block = "- ins_951_declared = True (from products.sqlite)"

    answer = ("[FACT] Diet Coke lists aspartame (INS 951) as a declared ingredient (products.sqlite, diet_coke).\n"
              "[FACT] FSSAI permits aspartame up to 700 ppm in carbonated beverages (fssai_knowledge_base.md, Chunk 50).")

    result = rm.faithfulness("is Diet Coke's sweetener within the legal limit", answer, chunks,
                              known_facts_block=known_facts_block)

    verify_call = next(c for c in _calls if c["call_name"] == "ragas_faithfulness_verify")

    check("faithfulness() with known_facts_block includes it in the verify call's context",
          "products.sqlite" in verify_call["user_message"] and "ins_951_declared" in verify_call["user_message"])
    check("faithfulness() still includes the real retrieved chunk text in the verify call's context",
          "700 ppm" in verify_call["user_message"])
    check("faithfulness() returns a real score when both claims verify",
          result["score"] == 1.0)

    # --- without known_facts_block, the judge context must NOT silently ---
    # --- gain the products.sqlite text (regression guard: the param is ---
    # --- genuinely optional-and-additive, not always-on) -----------------
    _calls.clear()
    rm.faithfulness("is Diet Coke's sweetener within the legal limit", answer, chunks)
    verify_call_no_kf = next(c for c in _calls if c["call_name"] == "ragas_faithfulness_verify")
    check("faithfulness() WITHOUT known_facts_block does not include it (the param is additive, not always-on)",
          "ins_951_declared" not in verify_call_no_kf["user_message"])
    check("faithfulness() without known_facts_block still includes the real chunk text",
          "700 ppm" in verify_call_no_kf["user_message"])

    # --- empty answer short-circuits before any complete() call ------------
    _calls.clear()
    empty_result = rm.faithfulness("q", "", chunks, known_facts_block=known_facts_block)
    check("an empty answer short-circuits with score=None and makes zero judge calls",
          empty_result["score"] is None and len(_calls) == 0)

finally:
    rm.complete = _original_complete

print()
if _failures:
    print(f"{len(_failures)} FAILURE(S):")
    for f in _failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All ragas_metrics regression checks passed.")
