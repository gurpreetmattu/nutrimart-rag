"""
conversation/state.py — the lightweight, structured conversation memory
problems.md Section 10 asks for: not the whole conversation, just the
important facts already established (product, topic/attribute in focus,
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
    }


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
    state["product_id"] = product_id
    state["product_name"] = product_name
    return state
