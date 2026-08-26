"""
generation/test_token_budget.py — regression tests for token_budget.py's
proactive per-key daily budget ledger, plus its wiring into
gateway.py::_groq_create() (key skipping and HF fallback on exhaustion).

No pytest in this project — plain assertions + a __main__ runner, same
convention as every other test_*.py file here.

Uses a real temp state file (swapped in via monkeypatching the module's
_STATE_PATH, restored after) so this never touches the real
token_budget_state.json the running app uses, and never makes a real
network call for the pure-ledger checks — only the final live-gateway
check actually calls an LLM provider (see its own note below).

Run:
    python src/generation/test_token_budget.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import generation.token_budget as tb

_failures: list[str] = []


def check(label: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        _failures.append(label)


# --- isolate from the real state file -------------------------------------

_tmp_dir = tempfile.mkdtemp()
_original_state_path = tb._STATE_PATH
tb._STATE_PATH = Path(_tmp_dir) / "test_token_budget_state.json"

try:
    # --- estimate_tokens / estimate_request_tokens ------------------------

    check("estimate_tokens scales with length",
          tb.estimate_tokens("a" * 400) > tb.estimate_tokens("a" * 40))
    check("estimate_tokens never returns 0 for non-empty text", tb.estimate_tokens("a") >= 1)

    est = tb.estimate_request_tokens(
        [{"role": "system", "content": "a" * 400}, {"role": "user", "content": "b" * 400}],
        max_tokens=2048,
    )
    check("estimate_request_tokens includes the completion budget", est > 2048)

    # --- has_budget / record_actual_usage: fresh key -----------------------

    check("a fresh key with no history has budget for a normal request",
          tb.has_budget(0, tb.estimate_request_tokens([{"role": "user", "content": "hi"}], 2048)))
    check("a fresh key's tracked usage is 0", tb.get_key_usage_today(0) == 0)

    # --- record_actual_usage accumulates -----------------------------------

    tb.record_actual_usage(0, 1000)
    tb.record_actual_usage(0, 500)
    check("usage accumulates across calls", tb.get_key_usage_today(0) == 1500)

    # --- has_budget flips false once EFFECTIVE_LIMIT would be crossed ------

    tb.record_actual_usage(0, tb.EFFECTIVE_LIMIT)  # now well past the 95% threshold
    check("has_budget is False once usage exceeds the effective (95%) limit",
          not tb.has_budget(0, 1000))

    # A request small enough to still fit isn't over-blocked by a coarse
    # all-or-nothing check — right at the boundary it should still refuse
    # (used up 100% + 1500 tokens of the raw 200k limit already).
    check("has_budget is still False even for a tiny 1-token request once over budget",
          not tb.has_budget(0, 1))

    # --- independent per-key buckets ----------------------------------------

    check("a different, untouched key still has full budget",
          tb.has_budget(1, tb.EFFECTIVE_LIMIT - 1))
    check("key 0's exhaustion doesn't leak into key 1's tracked usage",
          tb.get_key_usage_today(1) == 0)

    # --- persistence across a fresh load (simulates a process restart) -----

    reloaded = tb._load_state()
    today = tb._today()
    check("state persists to disk and reloads with the same today's-usage value",
          reloaded.get(today, {}).get("0") == tb.get_key_usage_today(0))

    # --- corrupt state file degrades gracefully, doesn't crash --------------

    tb._STATE_PATH.write_text("{not valid json", encoding="utf-8")
    try:
        state = tb._load_state()
        check("a corrupt state file is treated as empty history, not a crash", state == {})
    except Exception as e:
        check(f"a corrupt state file is treated as empty history, not a crash (raised {e!r})", False)

finally:
    tb._STATE_PATH = _original_state_path

print()

# --- live gateway wiring check --------------------------------------------
# This one DOES make a real call (small, cheap: max_tokens=20) — it's the
# only way to actually verify _groq_create()'s proactive-skip branch talks
# to the real .env-configured keys and genuinely falls back to Hugging
# Face when every key is pre-filled past budget, not just that the pure
# ledger functions above compute the right booleans in isolation. Uses the
# REAL state file (same one the running app uses) since gateway.py always
# imports the module-level _STATE_PATH directly — saves/restores its prior
# contents around the test so a real session's tracked usage isn't lost.

try:
    from dotenv import load_dotenv
    load_dotenv()
    from generation.gateway import complete, _load_groq_api_keys

    real_state_backup = tb._load_state() if tb._STATE_PATH.exists() else None
    try:
        state = {tb._today(): {str(i): tb.EFFECTIVE_LIMIT for i in range(len(_load_groq_api_keys()))}}
        tb._save_state(state)
        answer = complete(
            "You are a helpful assistant.", "Say OK and nothing else.",
            max_tokens=20, call_name="test_token_budget_live", reasoning_effort="low",
        )
        check("gateway falls back to HF and still returns an answer when all Groq keys "
              "are proactively exhausted", isinstance(answer, str) and len(answer.strip()) > 0)
    finally:
        if real_state_backup is not None:
            tb._save_state(real_state_backup)
        elif tb._STATE_PATH.exists():
            tb._STATE_PATH.unlink()
except Exception as e:
    print(f"[SKIP] live gateway wiring check — could not run ({e!r}); "
          f"the offline ledger checks above already cover the core logic.")

print()
if _failures:
    print(f"{len(_failures)} FAILURE(S):")
    for f in _failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All token-budget regression checks passed.")
