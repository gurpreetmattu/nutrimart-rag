"""
gateway.py — thin, single-entrypoint LLM call layer sitting in front of
llm.py's generate_answer()/rewrite_query(). Two real, motivated reasons to
have this rather than call Groq's SDK directly, both things this project
actually hit, not hypothetical:

1. **Automatic fallback on quota exhaustion.** Groq's 200,000 TPD limit was
   hit for real, multiple times, in one session (PHASE3_TESTING_LOG.md
   Findings 10 and 19) — every one of those runs just failed outright with
   no fallback. `complete()` catches Groq's RateLimitError specifically and
   retries once against a Hugging Face Inference API model
   (Qwen/Qwen2.5-7B-Instruct — ungated, ordinary instruct model) instead of
   giving up. This is genuinely tested against a real exhausted-quota
   state, not just written defensively and hoped to work.

2. **One place to log which provider actually served a call and what it
   cost.** `generate_answer()`/`rewrite_query()` used to build the Groq
   request inline and read `response.usage` inline — duplicated twice, and
   with no record of *which* provider handled a given call once a fallback
   exists. `complete()` centralizes this: every call's usage record now
   also carries `provider` ("groq" or "huggingface").

Deliberately NOT a general multi-provider abstraction (no LiteLLM, no
provider registry, no config-driven routing) — this project has exactly
two providers for one real reason (quota fallback), and building more than
that here would be exactly the kind of speculative abstraction CLAUDE.md
says not to add.
"""
import os

from groq import Groq, RateLimitError as GroqRateLimitError, BadRequestError as GroqBadRequestError
from huggingface_hub import InferenceClient

from generation.token_budget import (
    DAILY_TOKEN_LIMIT, AllKeysBudgetExhausted, estimate_request_tokens, has_budget, record_actual_usage,
)

GROQ_MODEL = "openai/gpt-oss-120b"
# Ungated, ordinary (non-reasoning) instruct model — chosen specifically so
# the fallback path has NO hidden reasoning-token overhead at all (unlike
# GROQ_MODEL, see PHASE3_TESTING_LOG.md Finding 19), and so a fallback call
# has predictable, bounded completion-token behavior even under the same
# max_tokens budget tuned for the reasoning model.
#
# Was "Qwen/Qwen2.5-7B-Instruct" until 2026-08-20: confirmed dead via a
# real call against this project's actual HF_TOKEN — "not supported by any
# provider you have enabled" on every provider tried, including HF's own
# hf-inference. Not a bug here; huggingface_hub now routes every model
# through HF's Inference Providers marketplace, and the 7B model this
# project originally picked is no longer served by any provider this
# token can reach. Verified 2026-08-20 that "Qwen/Qwen2.5-72B-Instruct" IS
# reachable with this token (a live chat_completion call succeeded) —
# swapped to that. Real cost: it's the 72B variant, not 7B, so slower and
# on HF's shared tier, not a dedicated free one — re-check the same way
# (a direct chat_completion call against the real token) if this ever
# breaks again, don't assume any specific model name stays servable.
HF_MODEL = "Qwen/Qwen2.5-72B-Instruct"

_groq_clients: list[Groq] | None = None
_groq_key_index = 0  # remembers the last-good key so we don't re-try dead ones every call
_hf_client: InferenceClient | None = None


def _load_groq_api_keys() -> list[str]:
    """
    GROQ_API_KEY, then GROQ_API_KEY_2, GROQ_API_KEY_3, ... (added 2026-08-21
    once a second/third free-tier key became available — each free key has
    its own independent 200k TPD limit, which was the single biggest
    constraint on iterating this session, e.g. PHASE3_TESTING_LOG.md
    Findings 10/19 and the repeated mid-eval quota exhaustion earlier
    today). Stops at the first missing numbered suffix, so GROQ_API_KEY_4
    etc. just needs adding to .env with no code change.
    """
    keys = []
    base = os.environ.get("GROQ_API_KEY")
    if base:
        keys.append(base)
    i = 2
    while True:
        key = os.environ.get(f"GROQ_API_KEY_{i}")
        if not key:
            break
        keys.append(key)
        i += 1
    return keys


def _get_groq_clients() -> list[Groq]:
    global _groq_clients
    if _groq_clients is None:
        keys = _load_groq_api_keys()
        if not keys:
            raise RuntimeError(
                "No Groq API key set. Get a free key at console.groq.com, "
                "then create a .env file with GROQ_API_KEY=gsk_... and load it "
                "before calling this, or export it in your shell."
            )
        _groq_clients = [Groq(api_key=k) for k in keys]
    return _groq_clients


def _groq_create(messages: list[dict], kwargs: dict):
    """
    Tries each configured Groq key in turn, starting from the last key that
    worked (not always key #1) so a call doesn't re-discover the same
    exhausted key on every single request once it's known to be dead this
    process.

    Before attempting a key, checks token_budget.has_budget() — a
    proactive, local-ledger estimate of whether this key has enough
    daily-quota headroom left for THIS request (see token_budget.py's
    docstring for why this is layered in front of, not instead of, the
    reactive handling below). A key without headroom is skipped with no
    API call at all — no wasted round-trip discovering what the local
    ledger already predicted. If every key is skipped this way,
    AllKeysBudgetExhausted is raised so the caller can fall back to HF
    exactly as it would for a real RateLimitError, just without paying for
    however many doomed requests that would have taken.

    Still catches GroqRateLimitError per key too — the local ledger can be
    wrong (another process spent this key's quota outside this ledger, or
    the character-count estimate undershot) — this is the real safety net,
    unchanged from before. Raises the final RateLimitError only once every
    attempted key has been tried and failed.
    """
    global _groq_key_index
    clients = _get_groq_clients()
    estimated_tokens = estimate_request_tokens(messages, kwargs.get("max_tokens", 0))
    last_err = None
    any_attempted = False
    for offset in range(len(clients)):
        idx = (_groq_key_index + offset) % len(clients)
        if not has_budget(idx, estimated_tokens):
            print(f"\n[gateway] Groq key #{idx + 1}/{len(clients)} skipped — proactive token-budget "
                  f"check predicts it's too close to its daily limit for this request (~{estimated_tokens} "
                  f"est. tokens).\n")
            continue
        any_attempted = True
        try:
            response = clients[idx].chat.completions.create(
                model=GROQ_MODEL, messages=messages, **kwargs,
            )
            _groq_key_index = idx
            usage = getattr(response, "usage", None)
            if usage is not None:
                record_actual_usage(idx, usage.total_tokens)
            return response
        except GroqRateLimitError as e:
            last_err = e
            # The API itself said no even though the local ledger thought
            # there was headroom — record the full daily limit as spent so
            # this key stops being retried for the rest of today, since the
            # exact remaining headroom isn't knowable from a 429 alone.
            record_actual_usage(idx, DAILY_TOKEN_LIMIT)
            if len(clients) > 1:
                print(f"\n[gateway] Groq key #{idx + 1}/{len(clients)} rate-limited, trying next key...\n")
            continue
    if not any_attempted:
        raise AllKeysBudgetExhausted(
            f"All {len(clients)} Groq key(s) are proactively judged too close to their daily "
            f"token budget for this request (~{estimated_tokens} est. tokens)."
        )
    raise last_err


def _get_hf_client() -> InferenceClient:
    global _hf_client
    if _hf_client is None:
        token = os.environ.get("HF_TOKEN")
        if not token:
            raise RuntimeError(
                "HF_TOKEN not set — the Groq fallback needs a Hugging Face "
                "Inference API token. Get a free one at huggingface.co/settings/tokens "
                "(read access is enough) and add HF_TOKEN=hf_... to .env."
            )
        _hf_client = InferenceClient(token=token)
    return _hf_client


def _record_usage(usage_out: list | None, call: str, provider: str, usage) -> None:
    if usage_out is None or usage is None:
        return
    reasoning_tokens = 0
    details = getattr(usage, "completion_tokens_details", None)
    if details is not None:
        reasoning_tokens = details.reasoning_tokens
    usage_out.append({
        "call": call,
        "provider": provider,
        "prompt_tokens": usage.prompt_tokens,
        "completion_tokens": usage.completion_tokens,
        "reasoning_tokens": reasoning_tokens,
        "total_tokens": usage.total_tokens,
    })


def complete_raw(
    messages: list[dict],
    max_tokens: int,
    call_name: str,
    reasoning_effort: str | None = None,
    usage_out: list | None = None,
    tools: list[dict] | None = None,
    tool_choice: str | dict | None = None,
):
    """
    Like complete(), but takes a full messages list (needed for a
    tool-calling loop's multi-turn shape: system, user, assistant-with-
    tool_calls, tool-result, ...) and returns the raw response message
    object instead of just its .content string, so a caller can inspect
    message.tool_calls. complete() is a thin wrapper over this for the
    existing single-turn system+user callers (generate_answer/
    rewrite_query), unchanged behavior for them.

    `tools`/`tool_choice` are passed through to both providers untouched
    when given — confirmed both `Groq.chat.completions.create()` and
    `InferenceClient.chat_completion()` accept these params directly
    (OpenAI-compatible `tools: list[{"type": "function", "function": {...}}]`
    shape) as of the SDK versions this project pins, 2026-08-21.
    """
    try:
        kwargs = {"max_tokens": max_tokens}
        if reasoning_effort is not None:
            kwargs["reasoning_effort"] = reasoning_effort
        if tools is not None:
            kwargs["tools"] = tools
        if tool_choice is not None:
            kwargs["tool_choice"] = tool_choice
        response = _groq_create(messages, kwargs)
        _record_usage(usage_out, call_name, "groq", response.usage)
        return response.choices[0].message
    except (GroqRateLimitError, AllKeysBudgetExhausted) as e:
        reason = "rate-limited" if isinstance(e, GroqRateLimitError) else "proactively judged over daily budget"
        print(f"\n[gateway] All Groq keys {reason} ({call_name}): {e}\n"
              f"[gateway] Falling back to Hugging Face ({HF_MODEL})...\n")
    except GroqBadRequestError as e:
        # tool_choice="required" (added 2026-08-21 to stop the model
        # silently declining to call any tool) can itself fail hard on
        # Groq's strict-decoding constrained generation for some inputs —
        # confirmed real: "Tool choice is required, but model did not call
        # a tool" (code tool_use_failed), not a rate limit, so it wasn't
        # caught by the branch above. Confirmed via direct repro (2026-08-21)
        # that this is a transient generation hiccup, not a systematic
        # per-query failure — the identical request reliably succeeds on a
        # second attempt — so retry "required" itself once (still forces a
        # real tool call, which produces a materially better answer than
        # "auto" silently returning none) before ever degrading to "auto".
        if tool_choice == "required" and "tool_use_failed" in str(e):
            print(f"\n[gateway] Groq tool_choice=required failed ({call_name}): {e}\n"
                  f"[gateway] Retrying with tool_choice=required again...\n")
            try:
                response = _groq_create(messages, kwargs)
                _record_usage(usage_out, call_name, "groq", response.usage)
                return response.choices[0].message
            except AllKeysBudgetExhausted:
                pass  # falls through to the shared HF fallback below
            except GroqBadRequestError as e2:
                if "tool_use_failed" not in str(e2):
                    raise
                print(f"\n[gateway] Groq tool_choice=required failed again ({call_name}): {e2}\n"
                      f"[gateway] Falling back to tool_choice=auto...\n")
                kwargs["tool_choice"] = "auto"
                try:
                    response = _groq_create(messages, kwargs)
                    _record_usage(usage_out, call_name, "groq", response.usage)
                    return response.choices[0].message
                except AllKeysBudgetExhausted:
                    pass  # falls through to the shared HF fallback below
        else:
            raise

    client = _get_hf_client()
    kwargs = {}
    if tools is not None:
        kwargs["tools"] = tools
    if tool_choice is not None:
        kwargs["tool_choice"] = tool_choice
    response = client.chat_completion(
        messages=messages, model=HF_MODEL, max_tokens=max_tokens, **kwargs,
    )
    _record_usage(usage_out, call_name, "huggingface", response.usage)
    return response.choices[0].message


def complete(
    system_prompt: str,
    user_message: str,
    max_tokens: int,
    call_name: str,
    reasoning_effort: str | None = None,
    usage_out: list | None = None,
) -> str:
    """
    Single entrypoint for every non-tool-calling LLM call in this project.
    Tries Groq first; on Groq's RateLimitError specifically (quota/rate
    exhaustion — not other error types, which should surface immediately
    rather than being masked by a fallback to a much weaker model) retries
    once against the Hugging Face fallback. Returns the response content
    string either way.

    `call_name` is a label ("generate_answer"/"rewrite_query") carried into
    the usage record, not behavior-affecting — lets a caller distinguish
    which real call a usage entry belongs to when usage_out accumulates
    entries from more than one call (e.g. a corrective retry).

    `reasoning_effort`, if given, is passed to Groq only (HF_MODEL is a
    non-reasoning model, has no such concept) — see GENERATION_REASONING_EFFORT
    in llm.py for the real-data-backed default.
    """
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    message = complete_raw(
        messages, max_tokens, call_name,
        reasoning_effort=reasoning_effort, usage_out=usage_out,
    )
    return message.content
