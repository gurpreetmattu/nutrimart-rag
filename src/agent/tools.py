"""
agent/tools.py — tool schemas + dispatch for ask_hybrid.py's tool-calling
loop (replaces routing/query_router.py::classify_intent() and its phrase
tables — see PHASE3_TESTING_LOG.md and the 2026-08-21 plan for why: every
routing bug that session was the same failure mode, a keyword list that
didn't anticipate one phrasing, which is structurally unfixable by adding
more phrases).

Every tool here is a thin wrapper over an EXISTING, already-correct data
function — no retrieval/SQL/comparison logic is reimplemented. The model
decides which tool(s) a question needs; each tool's own Python code still
does 100% deterministic, grounded lookups against products.sqlite/the KB,
exactly as before. This file only owns: (1) the JSON schemas the model sees,
(2) dispatching a structured tool call to the right existing function.

search_knowledge_base is NOT dispatched here — it needs ask_hybrid.py's
loaded resources (qdrant client, bm25 index, cross-encoder) and calling
retrieve_hybrid_with_retry() from here would create a circular import
(ask_hybrid.py -> agent.tools -> ask_hybrid.py). ask_hybrid.py's loop
special-cases that one tool name directly; this module only defines its
schema for the model to see.
"""
import sqlite3

from structured.product_facts import answer_product_fact, answer_ingredient_or_allergen, NUTRITION_FIELDS
from structured.product_comparison import answer_alternatives, answer_full_comparison

# Every field lookup_product_fact can resolve — mirrors what
# routing/query_router.py's NUTRITION_FIELD_PATTERNS/OTHER_FACT_PATTERNS
# used to gate via phrase matching; here it's just the enum of valid
# arguments, matching is entirely the model's job now.
_PRODUCT_FACT_FIELDS = sorted(NUTRITION_FIELDS | {
    "fssai_license", "ingredients_raw", "allergens", "pack_size", "brand", "category",
})

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_product_fact",
            "description": (
                "Look up ONE specific stored fact about the current product — a nutrition "
                "value (per serving/100g as stored), FSSAI license, full ingredient list, "
                "allergen declaration, pack size, brand, or category. Use this ONLY for a "
                "direct 'how much X' / 'what is the Y' question about THIS product's own "
                "value, not for checking whether a specific named ingredient/allergen is "
                "present (use check_ingredient_or_allergen for that). NEVER use this for a "
                "question mentioning other products, options, or alternatives — 'what ELSE', "
                "'other options', 'lower-X alternatives', 'anything better' all mean "
                "compare_products, even if the question also names a metric like calories or "
                "sugar that happens to match one of this tool's own fields."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "field": {"type": "string", "enum": _PRODUCT_FACT_FIELDS},
                },
                "required": ["field"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_ingredient_or_allergen",
            "description": (
                "Check whether a specific named ingredient or allergen (e.g. 'milk solids', "
                "'sugar', 'oats', 'peanut', 'caffeine') is actually DECLARED IN/PART OF the "
                "current product's own composition — AND, when the label discloses one, its "
                "actual quantity (e.g. 'Caffeine (10 mg/100g)'). Pass the name exactly as the "
                "user said it, even if misspelled or informally phrased — this does a fuzzy "
                "match against the product's real declared data, you do not need to normalize "
                "it yourself. Use this for 'does this contain X' / 'is there X in this' / "
                "'what is X' / 'HOW MUCH X does this have' questions naming a specific "
                "ingredient or allergen NOT already covered by lookup_product_fact's tracked "
                "nutrition fields (sugar/fat/protein/etc. — those still go to "
                "lookup_product_fact). Always try this tool for a product-specific quantity "
                "question before assuming a general regulatory limit answers it — a regulatory "
                "limit chunk states the MAXIMUM ALLOWED, never the product's actual amount; "
                "check the product's own declared data first. Do NOT use this for a "
                "serving/pairing/preparation question that "
                "merely MENTIONS a food word without asking whether it's an ingredient — e.g. "
                "'can I have this with milk', 'how should I eat this', 'what goes well with "
                "this' are asking about serving suggestions, not whether milk is IN the "
                "product; use search_knowledge_base for those instead (it may honestly come "
                "back with no answer if the KB doesn't cover serving suggestions, which is "
                "correct — don't force an unrelated ingredient-presence answer to a pairing "
                "question)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "The ingredient or allergen name as mentioned by the user."},
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_products",
            "description": (
                "Compare the current product against OTHER, not-yet-named products in the same "
                "category — a database lookup for 'what else is available'. Use for 'compare', "
                "'other options', 'what else', 'anything better/cheaper/lower-X', 'lowest "
                "sugar', 'which has less fat' — even when the question also names a specific "
                "metric (sugar, calories, saturated fat): naming a metric does NOT make this a "
                "lookup_product_fact question if the user is asking about OTHER products, not "
                "just this one. Do NOT use this for a question that evaluates a trade-off "
                "between two variants/products the user ALREADY named by name (e.g. 'should I "
                "pick the diet version instead of regular', 'is X better than Y') — that is a "
                "regulatory/nutrition judgment call, not a database alternatives lookup, so it "
                "needs search_knowledge_base instead (call compare_products too only if the "
                "user is separately asking for other database options as well). If "
                "the user named a specific metric "
                "(sugar, calories, saturated fat), pass it as criterion; if they just said "
                "'compare' or 'any alternatives' with no metric, pass criterion='none' — this "
                "returns a full side-by-side comparison across all tracked metrics rather than "
                "guessing or asking again."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "criterion": {"type": "string", "enum": ["sugar", "calories", "saturated_fat", "none"]},
                },
                "required": ["criterion"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": (
                "Search the regulatory/nutrition/ingredient knowledge base for general "
                "interpretation, regulatory rules, health/safety context, or 'why' questions "
                "that aren't answered by the product's own stored data — e.g. FSSAI limits, "
                "WHO nutrition guidance, what an additive is/does, whether something is legally "
                "permitted. Combine with lookup_product_fact first if the question also needs "
                "the product's own numbers (e.g. 'is this healthy' needs both the product's "
                "nutrition facts AND general guidance). Calling this tool is the decision that "
                "matters — the search itself always runs against the user's actual question "
                "text, not a rewritten query, so this tool takes no arguments."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
# `search_knowledge_base` deliberately takes no `query` argument — it used
# to (`{"query": "A focused search query for the knowledge base."}`), but
# that let the model's own reformulation silently steer retrieval away
# from what the user actually asked. Confirmed real 2026-08-24: for q07
# ("should I pick the diet version instead of regular"), the model rewrote
# the tool call to "diet coke vs regular coke which is healthier
# recommendation" — reasonable on its own, but it retrieved a completely
# different, unrelated candidate pool (Phosphoric Acid, a caffeine-limits
# chunk, generic ingredient entries — all near-zero rerank scores) instead
# of the two chunks this exact question was built around
# (`nutrition_knowledge_base.md` Chunk 8c + `fssai_knowledge_base.md`
# Chunk 5, both tagged `comparison_group: "sugar_vs_sweetener"`), silently
# defeating the comparison_group rescue mechanism (Finding 16) — which was
# built and verified against the LITERAL query text, before the LLM
# tool-calling migration (Finding 25) made query rewriting possible at
# all. Both ask_hybrid.py and ask_langchain_hybrid.py's tool-dispatch loops
# were changed to always retrieve using the real, already-follow-up-
# resolved user question instead of trusting this argument — any further
# reformulation still happens, just through retrieve_hybrid_with_retry()'s
# own separately-tuned rewrite_query() corrective-retry step (Finding 7),
# not an unconstrained rewrite made before retrieval even starts once.

# Exact-match sentinel dispatch_structured_tool returns when a
# product-specific tool is called with no product resolved — ask_hybrid.py
# detects this string to trigger the search_knowledge_base fallback below
# (2026-08-21 fix, see ask_hybrid.py's loop for why: the model sometimes
# calls a structured tool anyway for a context-free question despite the
# system prompt saying not to, and this used to be returned straight to
# the user as a dead-end instead of falling back to retrieval).
NO_PRODUCT_CONTEXT_MESSAGE = "[UNCERTAIN] No product is currently in context to look this up for."

# criterion arg (model-facing) -> internal criterion key structured/product_comparison.py expects
_CRITERION_ARG_MAP = {
    "sugar": "lower_sugar",
    "calories": "lower_calories",
    "saturated_fat": "lower_saturated_fat",
    "none": "same_category",
}

STRUCTURED_TOOL_NAMES = {"lookup_product_fact", "check_ingredient_or_allergen", "compare_products"}


def dispatch_structured_tool(tool_name: str, arguments: dict, product_id: str | None, conn: sqlite3.Connection) -> str:
    """
    Runs one of the three structured (non-retrieval) tools and returns its
    already-typed/cited answer string directly — these never need a second
    LLM synthesis call, same "instant, zero extra generation cost" property
    routing/query_router.py's classify_query() fast path had for the narrow
    cases it covered, now general to anything these three tools handle.
    """
    if product_id is None:
        return NO_PRODUCT_CONTEXT_MESSAGE

    if tool_name == "lookup_product_fact":
        field = arguments.get("field", "")
        if field not in _PRODUCT_FACT_FIELDS:
            return f"[UNCERTAIN] '{field}' is not a recognized product-fact field."
        return answer_product_fact(product_id, field, conn)

    if tool_name == "check_ingredient_or_allergen":
        return answer_ingredient_or_allergen(product_id, arguments.get("name", ""), conn)

    if tool_name == "compare_products":
        criterion_arg = arguments.get("criterion", "none")
        criterion = _CRITERION_ARG_MAP.get(criterion_arg, "same_category")
        if criterion == "same_category":
            return answer_full_comparison(product_id, conn)
        return answer_alternatives(product_id, criterion, conn)

    return f"[UNCERTAIN] Unknown tool '{tool_name}'."
