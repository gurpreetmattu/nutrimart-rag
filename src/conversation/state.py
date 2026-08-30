"""
conversation/state.py — lightweight, structured conversation memory: not
the whole conversation, just the important facts already established
(product, topic/attribute in focus,
and any concrete values already given), so a follow-up like "is this too
much?" doesn't need to re-derive them from scratch.

Pure functions, no I/O — the actual storage lives in api/session_store.py
(a process-local dict, same shape as api/security.py's rate-limit log).
Kept separate from that file since this shape is also directly useful to
CLI/eval callers of ask_langchain_hybrid.py::ask() that never touch the API
at all (its own conversation_state param takes this same dict shape).
"""


def default_state(product_id: str | None = None, product_name: str | None = None) -> dict:
    return {
        "product_id": product_id,
        "product_name": product_name,
        # attribute -> {"value": ..., "unit": ..., "source": ...}
        "known_facts": {},
        "active_topic": None,       # e.g. "nutrition", "ingredient", "allergen", "regulatory", "health"
        "active_attribute": None,   # e.g. "total_sugars_g" — the specific known_facts key in focus
        # bounded (user_text, assistant_text) pairs, oldest first — see
        # record_turn()'s docstring.
        "recent_turns": [],
    }


# Real conversation memory threaded into the generation prompt (see
# ask_langchain_hybrid.py::_build_generate_messages()) — added 2026-08-30
# after "tell me more, do not repeat the previous information" kept getting
# ignored: generation never saw what it actually SAID last turn, only a
# flat known_facts dict of numbers, so there was nothing for an explicit
# "don't repeat" instruction to check against. Bounded to the last
# RECENT_TURNS_LIMIT turns (and a rough char budget) rather than the whole
# conversation, so prompt size/token cost stays predictable in a long
# session instead of growing unboundedly.
RECENT_TURNS_LIMIT = 3
RECENT_TURNS_CHAR_BUDGET = 4000


def record_turn(state: dict, user_text: str, assistant_text: str) -> dict:
    turns = state.setdefault("recent_turns", [])
    turns.append((user_text, assistant_text))
    while len(turns) > RECENT_TURNS_LIMIT:
        turns.pop(0)
    while len(turns) > 1 and sum(len(u) + len(a) for u, a in turns) > RECENT_TURNS_CHAR_BUDGET:
        turns.pop(0)
    return state


def record_fact(state: dict, attribute: str, value, unit: str, source: str) -> dict:
    """Adds/overwrites one established fact. Also puts it in focus (active_attribute)."""
    state["known_facts"][attribute] = {"value": value, "unit": unit, "source": source}
    state["active_attribute"] = attribute
    return state


def set_active_topic(state: dict, topic: str, attribute: str | None = None) -> dict:
    state["active_topic"] = topic
    if attribute is not None:
        state["active_attribute"] = attribute
    return state


def set_product(state: dict, product_id: str, product_name: str) -> dict:
    """
    Switching products mid-conversation should NOT carry over the previous
    product's known_facts (that would be a real contradiction risk — e.g.
    answering a sugar question about product B with product A's number) —
    only reset when the product genuinely changes, not on every call, so a
    same-product follow-up keeps its established facts.
    """
    if state.get("product_id") != product_id:
        state["known_facts"] = {}
        state["active_attribute"] = None
        # A prior turn's history is about a DIFFERENT product once this
        # fires — keeping it risks the LLM blending facts across products
        # (the exact contradiction risk this function's own docstring
        # already covers for known_facts).
        state["recent_turns"] = []
    state["product_id"] = product_id
    state["product_name"] = product_name
    return state
