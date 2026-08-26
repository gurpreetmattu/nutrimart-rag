"""
api/security.py — Phase 8 prep: real application-layer guardrails for the
FastAPI layer, distinct from generation/groundedness.py's hallucination
guardrails. Before this file, api/main.py had none of these — no rate
limiting, no input length bounds, no injection-pattern check, confirmed by
reading main.py directly (it's plain Pydantic type validation and nothing
else). Scoped narrowly to what a single-instance portfolio demo actually
needs, not a general security framework:

- Rate limiting on /api/chat specifically, not the whole API — that's the
  one endpoint that spends real LLM-provider quota per call, and this
  project has hit real quota exhaustion multiple times in one day this
  session (PHASE3_TESTING_LOG.md Findings 10, 19, 22) purely from this
  session's own testing traffic. An unauthenticated public demo with no
  rate limit at all could exhaust both configured providers' free tiers
  from a handful of browser refreshes.
- Query length bounds (Pydantic Field, in main.py) — an unbounded query
  string becomes an unbounded prompt, which is both a cost/quota vector
  and, at extreme size, a resource-exhaustion vector.
- A best-effort prompt-injection heuristic — deliberately NOT presented as
  robust or complete (regex/keyword detection is trivially bypassable by
  a motivated attacker); see detect_prompt_injection()'s docstring for
  what it actually catches and why it flags rather than hard-blocks.

Explicitly NOT built here, and why: authentication (no user accounts, no
PII, no per-user data in this app — there's nothing to authenticate access
*to*); CORS configuration (no CORSMiddleware is registered in main.py,
which is the secure default — browsers already block cross-origin fetches
without it, so adding a permissive CORS policy would be a regression, not
a hardening). Both are deliberate scope decisions, not oversights.
"""
import re
import time
from collections import defaultdict, deque

# --- Rate limiting -----------------------------------------------------
#
# In-memory, single-process sliding-window limiter — no new dependency
# (slowapi et al. aren't installed and this app runs as one process, so a
# dict is enough; would need a shared store like Redis if this ever ran
# behind multiple worker processes). Keyed by client IP.

RATE_LIMIT_MAX_REQUESTS = 10
RATE_LIMIT_WINDOW_SECONDS = 60

_request_log: dict[str, deque] = defaultdict(deque)


def check_rate_limit(client_id: str, now: float | None = None) -> tuple[bool, int]:
    """
    Returns (allowed, retry_after_seconds). Evicts timestamps outside the
    sliding window before counting, so this is a true sliding window, not
    a fixed-bucket approximation that resets on a clock boundary.
    """
    now = now if now is not None else time.time()
    log = _request_log[client_id]

    while log and log[0] <= now - RATE_LIMIT_WINDOW_SECONDS:
        log.popleft()

    if len(log) >= RATE_LIMIT_MAX_REQUESTS:
        retry_after = int(RATE_LIMIT_WINDOW_SECONDS - (now - log[0])) + 1
        return False, retry_after

    log.append(now)
    return True, 0


# --- Prompt-injection heuristic -----------------------------------------
#
# Deliberately narrow: only patterns that are near-unambiguous attempts to
# override system instructions, not general suspicious words. This KB is
# about food safety/regulation, where words like "ignore the label" or
# "disregard the packaging claim" are completely legitimate user language
# — a blunt keyword blocklist would misfire constantly on real questions.
# Every pattern here specifically targets overriding THIS ASSISTANT's own
# instructions/identity/role, not generic imperative language.
_INJECTION_PATTERNS = [
    re.compile(r"\bignore\s+(all\s+|any\s+|the\s+)?(previous|prior|above|preceding)\s+instructions?\b", re.IGNORECASE),
    re.compile(r"\bdisregard\s+(your|the)\s+(system\s+)?(prompt|instructions?|rules?)\b", re.IGNORECASE),
    re.compile(r"\byou\s+are\s+now\s+(a|an)\b", re.IGNORECASE),
    re.compile(r"\bpretend\s+(you('re| are)|to\s+be)\s+(a|an)\b", re.IGNORECASE),
    re.compile(r"\breveal\s+(your\s+)?(system\s+)?(prompt|instructions)\b", re.IGNORECASE),
    re.compile(r"\bnew\s+instructions?\s*:", re.IGNORECASE),
    re.compile(r"\bact\s+as\s+(if\s+you('re| are)\s+)?(a|an)\b.{0,30}\b(not\s+bound|no\s+rules|unfiltered)\b", re.IGNORECASE),
]


def detect_prompt_injection(query: str) -> bool:
    """
    Best-effort, NOT a real defense against a motivated attacker — regex
    matching on an instruction-override pattern is trivially bypassed by
    paraphrasing, translation, encoding, or splitting the pattern across
    turns. What this DOES catch: the common, low-effort "ignore your
    instructions" / "you are now X" style attempts that show up in casual
    misuse or low-effort red-teaming. Real defense against a motivated
    attacker needs the same discipline generation/llm.py's SYSTEM_PROMPT
    already applies structurally (only answer from retrieved context,
    typed claims, no fabrication) — this heuristic is a cheap first line,
    not a replacement for that. Callers should flag/log a match, not
    treat it as a hard security boundary.
    """
    return any(p.search(query) for p in _INJECTION_PATTERNS)
