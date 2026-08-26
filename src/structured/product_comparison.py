"""
structured/product_comparison.py — problems.md Problem 8/Section 14: "What
is the alternative to this?" is a product-recommendation question, not a
knowledge-base question. Same no-LLM-call, direct-SQL pattern as
structured/product_facts.py (reuses its NUTRITION_LABELS rather than
re-deriving unit/label text) — routing/query_router.py::classify_intent()
routes "alternative_recommendation"/"product_comparison" here directly,
bypassing KB retrieval entirely, the same short-circuit shape ask_hybrid.py
already uses for the product_fact route.

No `price` column exists in products.sqlite (confirmed against the real
schema) — comparisons are limited to what's actually stored: category and
the nutrition_json fields.
"""
import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from structured.product_facts import get_product_row, NUTRITION_LABELS

# criterion -> nutrition.values key. "same_category" has no field (handled
# separately below — it's a listing, not a sort).
CRITERION_FIELDS = {
    "lower_sugar": "total_sugars_g",
    "lower_calories": "energy_kcal",
    "lower_saturated_fat": "saturated_fat_g",
}

# criterion -> phrases that mean the user explicitly named this criterion in
# the query text itself, e.g. "compare these by sugar" / "compare calories".
_CRITERION_PHRASES: dict[str, list[str]] = {
    "lower_sugar": ["sugar"],
    "lower_calories": ["calorie", "energy"],
    "lower_saturated_fat": ["saturated fat"],
}


def infer_criterion(query: str, active_attribute: str | None) -> str:
    """
    Confirmed real bug 2026-08-21: this used to only look at
    conversation_state's active_attribute (problems.md Section 14's
    default-to-topic-in-focus behavior) and never the query text itself —
    so "compare these products by sugar" was silently ignored and always
    fell back to the generic same_category listing, identically on every
    call, regardless of what the user actually typed. Explicit text takes
    priority now ("compare ... by sugar" should never be second-guessed by
    stale conversation state); active_attribute is still the fallback for
    an underspecified "compare these" with a nutrition topic already in
    focus from an earlier turn, and "same_category" (a bare listing) is
    the last resort when neither signal is available.
    """
    q = (query or "").lower()
    for criterion, phrases in _CRITERION_PHRASES.items():
        if any(p in q for p in phrases):
            return criterion

    for criterion, field in CRITERION_FIELDS.items():
        if field == active_attribute:
            return criterion

    return "same_category"


def find_alternatives(product_id: str, criterion: str, conn: sqlite3.Connection, limit: int = 3) -> list[dict]:
    row = get_product_row(product_id, conn)
    if row is None:
        return []

    candidates = conn.execute(
        "SELECT * FROM products WHERE category = ? AND product_id != ?",
        (row["category"], product_id),
    ).fetchall()

    field = CRITERION_FIELDS.get(criterion)
    if field is None:  # "same_category" or an unrecognized criterion
        return [{"product_id": c["product_id"], "name": c["name"]} for c in candidates[:limit]]

    own_value = json.loads(row["nutrition_json"] or "{}").get("values", {}).get(field)

    results = []
    for c in candidates:
        value = json.loads(c["nutrition_json"] or "{}").get("values", {}).get(field)
        if value is None:
            continue
        # Only genuinely lower — a candidate with an equal or higher value
        # isn't an "alternative" for this criterion, it just happens to
        # share a category. Skipped silently if own_value is unknown too
        # (nothing to compare against, not worth guessing).
        if own_value is not None and value >= own_value:
            continue
        results.append({"product_id": c["product_id"], "name": c["name"], "value": value, "field": field})

    results.sort(key=lambda r: r["value"])
    return results[:limit]


def answer_full_comparison(product_id: str, conn: sqlite3.Connection, limit: int = 3) -> str:
    """
    Real side-by-side comparison across all three tracked criteria (sugar,
    calories, saturated fat) — for when the user explicitly asks to
    "compare" but doesn't name a specific metric.

    Confirmed real gap 2026-08-21: an explicit "OK COMPARE" (intent ==
    "product_comparison") with no named criterion used to fall into the
    exact same bare-name listing as "any better alternative?" (intent ==
    "alternative_recommendation") with no criterion — repeating the
    identical "let me know if you'd like these compared by..." prompt
    right back at a user who had just explicitly asked to compare, instead
    of actually comparing anything. That bare listing is a reasonable
    response to a vague alternative-seeking question (inviting the user to
    narrow an ambiguous "better"); it is not a reasonable response to an
    explicit "compare" command, which should always produce a real
    comparison — defaulting to all three tracked metrics when no specific
    one is named, rather than asking again.
    """
    row = get_product_row(product_id, conn)
    if row is None:
        return f"[UNCERTAIN] No product record found for '{product_id}' in products.sqlite."

    name = row["name"]
    candidates = conn.execute(
        "SELECT * FROM products WHERE category = ? AND product_id != ?",
        (row["category"], product_id),
    ).fetchall()[:limit]

    if not candidates:
        return (f"[UNCERTAIN] No other {row['category']} products in the catalog were found to "
                f"compare {name} against (products.sqlite, {product_id}).")

    own_values = json.loads(row["nutrition_json"] or "{}").get("values", {})

    lines = []
    for field in CRITERION_FIELDS.values():
        label, unit = NUTRITION_LABELS.get(field, (field, ""))
        own_v = own_values.get(field)
        own_str = f"{own_v}{unit}" if own_v is not None else "unknown"
        parts = []
        for c in candidates:
            c_values = json.loads(c["nutrition_json"] or "{}").get("values", {})
            v = c_values.get(field)
            parts.append(f"{c['name']} {v}{unit}" if v is not None else f"{c['name']} unknown")
        lines.append(
            f"[FACT] {label} — {name} {own_str} vs. " + "; ".join(parts)
            + f" (products.sqlite, {product_id})."
        )

    # One [FACT]-tagged line per criterion (2026-08-21, was one giant
    # " | "-joined single line) — confirmed real complaint on the
    # Kellogg's Chocos "any better alternative to this?" conversation:
    # a single run-on line covering all three metrics reads as a wall of
    # text, especially once rendered in the compact chat UI. Separate
    # lines match how every other multi-claim answer in this project is
    # structured (generate_answer()'s own typed-claim output is always
    # one claim per line) instead of being a one-off format.
    return "\n".join(lines)


def answer_alternatives(product_id: str, criterion: str, conn: sqlite3.Connection) -> str:
    """
    [FACT]-tagged, cited to products.sqlite — same claim-typing contract
    as product_facts.py's answer_product_fact(), so downstream display
    code (consumer_view.py, groundedness.py) doesn't need a third format.
    """
    row = get_product_row(product_id, conn)
    if row is None:
        return f"[UNCERTAIN] No product record found for '{product_id}' in products.sqlite."

    name = row["name"]
    alternatives = find_alternatives(product_id, criterion, conn)

    if not alternatives:
        return (f"[UNCERTAIN] No other {row['category']} products in the catalog were found as "
                f"alternatives to {name} for this comparison (products.sqlite, {product_id}).")

    field = CRITERION_FIELDS.get(criterion)
    if field is None:
        names = ", ".join(a["name"] for a in alternatives)
        return (f"[FACT] Other {row['category']} products in the catalog include: {names}. "
                f"Let me know if you'd like these compared by sugar, calories, or saturated fat "
                f"(products.sqlite, {product_id}).")

    label, unit = NUTRITION_LABELS.get(field, (field, ""))
    parts = [f"{a['name']} ({a['value']}{unit} {label})" for a in alternatives]
    return (f"[FACT] Lower-{label}-than-{name} options in the same category: "
            f"{'; '.join(parts)} (products.sqlite, {product_id}).")
