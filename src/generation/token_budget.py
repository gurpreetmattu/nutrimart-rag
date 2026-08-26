"""
generation/token_budget.py — proactive per-key daily token budget for
gateway.py's Groq calls.

Problem this solves: gateway.py's existing fallback (see its own docstring)
is REACTIVE — it only learns a key is exhausted when Groq actually returns
a 429 RateLimitError, after a full round-trip. With multi-key rotation that
means a degraded request can burn several dead-key round-trips (each one
real latency) before landing on a live key or the HF fallback. This module
tracks each key's REAL cumulative spend for the current UTC day (Groq's
free-tier 200,000 TPD limit resets daily — exact reset time isn't published
for this tier, UTC midnight is the documented/observed convention) and lets
gateway.py skip a key BEFORE sending a request, once its tracked usage plus
a conservative estimate of the upcoming call would breach the limit.

State is a small JSON file (not in-memory) so the budget survives process
restarts — this project's dev server gets restarted often during a session,
and an in-memory-only counter would silently reset and stop protecting
anything.

Two honest limitations, stated plainly rather than hidden:
1. The token estimate for an outgoing request is a rough character-count
   heuristic (len(text) // CHARS_PER_TOKEN_ESTIMATE), not the model's real
   tokenizer — GROQ_MODEL isn't an OpenAI model, so pulling in tiktoken
   would produce a plausible-looking but still-wrong count, not a
   genuinely correct one, for the cost of a new dependency. SAFETY_MARGIN
   below exists specifically to compensate for the estimate being
   approximate, not exact.
2. This only tracks usage this app has itself made (and recorded) into the
   shared state file — it can't see quota consumed by, e.g., someone
   curling Groq directly with the same key outside this app. It's a
   best-effort local ledger, not a live query against Groq's own account
   dashboard (no such API exists on the free tier).

This is a pre-flight check layered IN FRONT OF the existing reactive
RateLimitError handling in gateway.py, not a replacement for it — the
reactive catch stays as the real safety net for exactly the cases this
estimate can't see (limitation 2 above, or the estimate simply being
wrong on a given request).
"""
import json
from datetime import datetime, timezone
from pathlib import Path

# src/generation/token_budget.py -> parent.parent.parent is the project root
_STATE_PATH = Path(__file__).resolve().parent.parent.parent / "token_budget_state.json"

# Groq's documented free-tier limit for this project's keys (see
# gateway.py's _load_groq_api_keys docstring) — each key has its own
# independent budget.
DAILY_TOKEN_LIMIT = 200_000

# Stop proactively using a key once it's within 5% of its daily limit,
# rather than cutting it exactly at 200,000 — leaves headroom for the
# character-count estimate below being an approximation, not a real
# tokenizer count.
SAFETY_MARGIN = 0.95
EFFECTIVE_LIMIT = int(DAILY_TOKEN_LIMIT * SAFETY_MARGIN)

# Rough English-text heuristic (~4 chars/token), the same rule of thumb
# OpenAI's own docs use for ballpark estimates without a real tokenizer.
# Deliberately conservative direction doesn't matter much here since
# SAFETY_MARGIN already absorbs estimate error either way.
CHARS_PER_TOKEN_ESTIMATE = 4


def _today() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def _load_state() -> dict:
    if not _STATE_PATH.exists():
        return {}
    try:
        return json.loads(_STATE_PATH.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        # Corrupt/partial state file (e.g. a killed process mid-write) must
        # never crash the app over what's just a soft usage estimate —
        # treat it the same as no history and let it rebuild.
        return {}


def _save_state(state: dict) -> None:
    try:
        _STATE_PATH.write_text(json.dumps(state), encoding="utf-8")
    except OSError:
        # Same reasoning as _load_state: this ledger is a best-effort
        # optimization, not a correctness-critical store. A failed write
        # (e.g. read-only filesystem) should degrade to "no proactive
        # check," not break the actual LLM call.
        pass


def estimate_tokens(text: str) -> int:
    return max(1, len(text) // CHARS_PER_TOKEN_ESTIMATE)


def estimate_request_tokens(messages: list[dict], max_tokens: int) -> int:
    """
    Conservative upper-bound estimate for one request: every message's
    content (prompt side) plus the full `max_tokens` completion budget
    (the model may not use all of it, but a pre-flight check has to plan
    for the case it does — the actual spend gets reconciled afterward via
    record_actual_usage, which always overrides this estimate with the
    real number from the API response).
    """
    prompt_text = "".join(m.get("content") or "" for m in messages)
    return estimate_tokens(prompt_text) + max_tokens


def get_key_usage_today(key_index: int) -> int:
    state = _load_state()
    day = state.get(_today(), {})
    return day.get(str(key_index), 0)


def has_budget(key_index: int, estimated_tokens: int) -> bool:
    return get_key_usage_today(key_index) + estimated_tokens <= EFFECTIVE_LIMIT


def record_actual_usage(key_index: int, total_tokens: int) -> None:
    """
    Called after every real Groq call with the response's real
    usage.total_tokens — this is what actually keeps the ledger accurate
    over time; estimate_request_tokens() only ever informs the pre-flight
    decision, never gets written to the ledger itself.
    """
    if total_tokens is None:
        return
    state = _load_state()
    today = _today()
    day = state.setdefault(today, {})
    day[str(key_index)] = day.get(str(key_index), 0) + total_tokens
    # Drop any stale prior-day entries so the file doesn't grow forever —
    # only today's tallies are ever read.
    for stale_day in [d for d in state if d != today]:
        del state[stale_day]
    _save_state(state)


class AllKeysBudgetExhausted(Exception):
    """
    Raised by gateway.py's key-selection loop when every configured Groq
    key is proactively judged too close to its daily limit for the
    upcoming request — distinct from GroqRateLimitError (which means Groq
    itself rejected a request that was actually sent) so callers can tell
    "we predicted this and skipped the round-trip entirely" apart from
    "we tried and Groq said no," while still handling both the same way
    (fall back to the HF provider).
    """
