"""
query_router.py — Phase 5 v1: routes a query to either the SQLite
product-fact path or the existing (still Phase-3-naive) retrieval path.

This is the fix for PHASE3_TESTING_LOG.md Finding 6 ("no query routing —
product-fact questions like calorie counts and license numbers went
through vector retrieval and correctly came back [UNCERTAIN] instead of
being answered directly").

Deliberately naive, same spirit as the Phase 3 baseline files: substring
and whole-word keyword matching, no ML classifier, no LLM call. Good
enough to fix q12/q13 in src/eval/test_questions.py and similar direct
lookups — not a general-purpose intent classifier. A regulatory/
interpretive/comparative query that happens to name a product (e.g. "is
Diet Coke's sweetener within the legal limit") must still go to
retrieval, so REGULATORY_OVERRIDE_TERMS always wins over a fact-field
match.

This module's actual scope narrowed on 2026-08-21: an LLM tool-calling
loop (ask_hybrid.py) now handles everything that isn't a confident,
unambiguous product-fact lookup — see that file's own migration note.
classify_query() below (the product_fact/retrieval split) is the one
piece that survived unchanged, kept as a pure cost optimization for the
cases it's genuinely confident about; classify_intent() and its
supporting phrase tables/data-driven matchers, which used to run a
second, finer-grained classification within the retrieval route, were
confirmed fully unreferenced and deleted outright 2026-08-22 (not just
retired-in-place) — the tool-calling loop's real language understanding
replaced what they did, only better.
"""
import difflib
import re
import sys
from pathlib import Path
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import sqlite3

TOKEN_RE = re.compile(r"[a-z0-9]+")

# Any of these appearing in the query forces retrieval, even if a product
# name and a fact-field keyword both match — they're the signal that the
# question is about a rule, comparison, or interpretation, not a stored
# fact column.
REGULATORY_OVERRIDE_TERMS = [
    "allowed", "permitted", "permissible", "limit", "legal", "safe",
    "safety", "regulation", "regulatory", "standard", "should i",
    "why does", "why do", "why is", "compare", "comparison",
    "difference between", "health concern", "risk", "instead of",
    "concern",
    # Comparison/alternative-seeking phrasing (added 2026-08-21): without
    # these, a query like "wat abt other options with lower calries" gets
    # intercepted here as a product_fact fast-path lookup (fuzzy-matches
    # "calries" -> energy_kcal) before the tool-calling loop ever sees it,
    # even though the tool loop's own compare_products-vs-lookup_product_fact
    # disambiguation (agent/tools.py) was already fixed and verified correct
    # in isolation — confirmed real via eval_run_hybrid's conversation
    # eval c02 turn 2. This fast path has no comparison mechanism of its
    # own, so any of these must always fall through to the tool loop.
    "other option", "other options", "alternative", "alternatives",
    "what else", "anything else", "any other",
    # "claim" (added 2026-08-24, real bug — RAGAS eval q27): "can
    # Britannia Brown Bread claim it has as much fibre as an apple"
    # matches NUTRITION_FIELD_PATTERNS' "fibre" keyword with no override
    # term present, so it fast-pathed to a bare dietary_fibre_g lookup
    # (2.8g) — completely ignoring that the actual question is whether a
    # marketing CLAIM is legally supportable (a claims_advertising-doc_type
    # regulatory question, fssai_knowledge_base.md Chunk 23's equivalence-
    # claim rule), not a request for the raw number. "claim" substring-
    # matches "claims" too (this list is checked via `term in q`), so one
    # entry covers both.
    "claim",
    # Value-judgment phrasing (added 2026-08-21): a compound question like
    # "how much sodium is there in this and is it too much?" still matches
    # a NUTRITION_FIELD_PATTERNS keyword ("sodium"), so without this it's
    # intercepted here and answered with ONLY the bare number — the "is it
    # too much" half of the question never reaches the tool loop's
    # search_knowledge_base/health-judgment handling at all. Confirmed real
    # (Kellogg's Chocos conversation) on both the original compound
    # question and the plain follow-up "is this too much?" (which
    # resolve_followup() rewrites to lead with the same fact, still
    # containing "too much" verbatim, so this term catches both phrasings
    # with one entry).
    "too much",
    # "good source of"/"rich in"/"high in"/"low in" (added 2026-08-26,
    # Finding 40 — a proactive stress-test batch run right after a live
    # vegan-question bug report): "is this a good source of protein?"
    # matches NUTRITION_FIELD_PATTERNS' "protein" keyword with no override
    # term present, so it fast-pathed to a bare protein_g lookup (10.0g) —
    # completely ignoring that this is the SAME shape of regulatory
    # nutrient-content-claim question as "claim" above (FSSAI's real
    # "source"/"high in" claim thresholds, fssai_knowledge_base.md Chunk 22),
    # just phrased without the literal word "claim". Confirmed real: this
    # fast path resolved via `route="product_fact"` before the tool-calling
    # loop (and its own, separately-broadened _CLAIM_ELIGIBILITY_RE in
    # ask_hybrid.py) ever got a chance to see the query at all — the
    # ask_hybrid.py-level fix alone was insufficient, same two-layer shape
    # as q27's original router+tool-loop bug pair.
    "good source of", "rich in", "high in", "low in", "excellent source",
]

# General structural override (added 2026-08-21 audit) — replaces the
# ever-growing approach of adding one more judgment WORD to
# REGULATORY_OVERRIDE_TERMS every time a new phrasing is reported ("too
# much" above was itself exactly that: a one-off word added for one
# reported bug). "how much sodium is there in this and is it too much?"
# only got fixed by adding "too much"; a structurally identical question
# using different judgment words ("how much protein is in this and is
# that enough for me?", "does this have a license and is it legitimate?")
# would have kept slipping through as a new bug report, one word list
# entry at a time, forever — confirmed real by testing several
# never-explicitly-added phrasings during the 2026-08-21 audit, all of
# which reproduced the same failure shape. The actual structural signal
# isn't any particular word, it's the SHAPE: a fact-lookup clause with a
# second clause tacked on via a conjunction ("and is"/"and does"/"but
# is"/etc.) — that second clause is a judgment/follow-up question this
# deterministic fast path has no way to answer, regardless of which words
# it uses, so defer to the tool loop for ANY compound question shaped
# like this rather than trying to enumerate every judgment phrase.
# Verified against every product_fact eval case in test_questions.py
# (q12-q17): none of those single-clause questions match this pattern.
_COMPOUND_CLAUSE_RE = re.compile(
    # "whether" added 2026-08-22 (proactive stress test, not a live bug
    # report): "tell me the calories and whether that fits my diet" is the
    # same compound-clause shape but with "and whether" instead of "and
    # is/does" — found before it could be reported.
    r"\b(?:and|but)\s+(?:is|does|do|are|was|were|will|would|should|can|could|whether)\b",
    re.IGNORECASE,
)

# Same structural-override principle as _COMPOUND_CLAUSE_RE, for a
# different shape: a personal health-condition statement ("I am allergic
# to milk", "I have low blood sugar", "I am diabetic") followed by ANY
# verb phrasing asking whether to consume the product ("should I buy",
# "can I consume", "can I eat", "is it safe" — infinite variations).
# Confirmed real 2026-08-21: "i am allergen to milk should i buy it?" and
# "i have low blood sugar level can i consume it?" both got answered with
# a bare fact/allergen dump, completely ignoring the stated condition —
# neither matched _HEALTH_JUDGMENT_RE's word list (which only covered
# "should i buy/eat/choose/pick/get", not "can i consume") or
# _COMPOUND_CLAUSE_RE (no "and/but is/does" conjunction in either query).
# Enumerating every possible verb phrase after a health-condition
# statement is the same unwinnable game as the word lists these two
# regexes already replaced — the actual signal is the CONDITION statement
# itself: once a user states a personal health condition, essentially
# anything that follows is implicitly asking "is this okay for me,"
# regardless of the exact verb used, so defer to the tool loop
# unconditionally whenever this pattern matches.
_HEALTH_CONDITION_RE = re.compile(
    # Broadened 2026-08-22 (proactive stress test, not a live bug report —
    # found before being reported): the original only covered first-person
    # "i am/i have" with "allerg"/"diabet" stems. Testing synthetic
    # phrasings found 3 real gaps in one pass: "i SUFFER FROM high blood
    # pressure" (different verb), "MY CHILD has a nut allergy" (third-person
    # — arguably the more important case for allergy safety), and "i am
    # LACTOSE INTOLERANT" (a condition stem, "intoleran", not covered at
    # all). Restructured as SUBJECT + VERB + CONDITION-STEM instead of
    # enumerating whole phrases, so future verb/subject variations (e.g.
    # "my son suffers from...") are covered structurally rather than
    # needing their own explicit entry.
    # Re-fixed within the same pass, before shipping: the first draft above
    # (subject + verb + optional article + condition-stem, no filler
    # allowed) dropped the "i'm" contraction entirely and couldn't handle
    # a descriptive word between the verb and the condition ("a NUT
    # allergy", "LACTOSE intolerant") — caught by re-running the same
    # stress test against my own fix before considering it done, not by a
    # user report.
    r"\b(?:i'm|i\s+am|i\s+have|i\s+suffer(?:s)?\s+from"
    r"|my\s+(?:child|kid|son|daughter|wife|husband|baby|family\s+member)\s+(?:is|has|suffers?\s+from))\b"
    r".{0,20}?\b\w*(?:allerg\w*|diabet\w*|intoleran\w*|celiac\w*|coeliac\w*)\b"
    r"|\bi\s+(?:have|suffer(?:s)?\s+from)\s+(?:low|high)\s+blood\s+(?:sugar|pressure)\b"
    r"|\bi(?:'m|\s+am)\s+pregnant\b",
    re.IGNORECASE,
)

# phrase (matched as a plain substring of the lowercased query) -> the
# nutrition.values key in products_compiled.json / the nutrition_json
# column. Order matters only in that more specific phrases should be
# checked before their more general overlaps end up mattering — none
# currently overlap, so a simple first-match-wins scan is fine.
NUTRITION_FIELD_PATTERNS: list[tuple[list[str], str]] = [
    (["calorie", "energy"], "energy_kcal"),
    (["added sugar"], "added_sugars_g"),
    (["total sugar", "sugar content", "how much sugar", "sugar in"], "total_sugars_g"),
    (["saturated fat"], "saturated_fat_g"),
    (["trans fat"], "trans_fat_g"),
    (["total fat", "fat content", "fat in"], "total_fat_g"),
    (["protein"], "protein_g"),
    (["carbohydrate", "carb content", "carbs in"], "carbohydrate_g"),
    (["sodium", "salt content"], "sodium_mg"),
    (["cholesterol"], "cholesterol_mg"),
    # Added 2026-08-22: dietary_fibre_g turns out to genuinely exist in
    # nutrition_json for 8/23 catalog products (confirmed via direct data
    # check) — test_questions.py q20 previously documented "the nutrition
    # schema doesn't even have a fibre_g key" as a permanent, accepted gap,
    # which was true when written but is now stale: the real data has the
    # field, it was just never wired into field-matching.
    # "does this contain fibre?"/"does this contain dietary fibre?" for
    # Britannia Brown Bread (which DOES have this field) was answering
    # "'fibre' was not found among declared ingredients or allergens" —
    # misleadingly implying the bread has no fibre at all, when the real
    # issue was just that this lookup path didn't exist yet.
    # answer_product_fact()/get_all_nutrition_facts() already handle a
    # per-product missing key gracefully ([UNCERTAIN], not a crash) for
    # the other 15 products that don't track it.
    (["dietary fibre", "dietary fiber", "fibre", "fiber"], "dietary_fibre_g"),
    # Added 2026-08-22, same systematic-audit pass as dietary_fibre_g above
    # — these 8 fields also genuinely exist in nutrition_json for at least
    # one catalog product (caffeine_mg confirmed for Diet Coke/Coca-Cola,
    # the others for various fortified/whole-grain products) but had no
    # matching phrase at all. "total salt" (not bare "salt") deliberately
    # avoids colliding with the existing "salt content" -> sodium_mg
    # phrase above — total_salt_g and sodium_mg are two DIFFERENT declared
    # values (only one product, Yogabar, tracks total_salt_g separately),
    # not alternate phrasings of the same field.
    (["caffeine"], "caffeine_mg"),
    (["calcium"], "calcium_mg"),
    (["iron"], "iron_mg"),
    (["potassium"], "potassium_mg"),
    (["vitamin c"], "vitamin_c_mg"),
    (["monounsaturated fat", "mono-unsaturated fat", "mono unsaturated fat"], "mono_unsaturated_fat_g"),
    (["polyunsaturated fat", "poly-unsaturated fat", "poly unsaturated fat"], "poly_unsaturated_fat_g"),
    (["energy from fat", "calories from fat"], "energy_from_fat_kcal"),
    (["total salt"], "total_salt_g"),
]

# Non-nutrition fact fields: phrase -> logical field name, resolved to a
# products-table column (or pair of columns) in structured/product_facts.py.
OTHER_FACT_PATTERNS: list[tuple[list[str], str]] = [
    (["license", "licence"], "fssai_license"),
    (["ingredient list", "ingredients does", "ingredients in", "ingredients raw",
      "what's in", "what is in"], "ingredients_raw"),
    (["allergen", "contains milk", "contains wheat", "contains nuts",
      "contains soy", "may contain"], "allergens"),
    (["pack size", "net weight", "how much does it weigh", "how big is",
      "weigh"], "pack_size"),
    (["what brand", "which brand", "who makes", "which company"], "brand"),
    (["what category", "which category"], "category"),
]

# A bare generic ingredient-presence catch-all ("contain" -> ingredients_raw,
# dumping the full raw ingredient string) used to live here, added
# 2026-08-20 before agent/tools.py::check_ingredient_or_allergen existed —
# at the time it was a real improvement over falling through to naive
# retrieval. Retired 2026-08-21: now that the tool-calling loop has a
# proper per-ingredient fuzzy-match handler, this deterministic catch-all
# is strictly worse — confirmed real for "does this contain any vitamins?"
# and "does this product contain too much sugar?" (Kellogg's Chocos
# conversation), both intercepted here before the tool loop ever ran and
# got the entire raw ingredient list dumped back instead of a direct,
# concise answer (or, for the "too much sugar" case, instead of the
# health-judgment interpretation the question actually needed). These
# questions now correctly fall through to the tool-calling loop.

# Naive doc_type intent hint for the hybrid retriever (retrieval/search_hybrid.py).
# Used only as a soft RRF score boost there, never a hard filter — the KB's
# own doc_type coverage has gaps (see ingestion/parse_kb.py's preamble-
# default fix) and a wrong guess here shouldn't make the correct chunk
# unreachable, same reasoning as find_product()'s refuse-to-guess-on-ties
# behavior above.
DOC_TYPE_PATTERNS: list[tuple[list[str], str]] = [
    (["can a product say", "can it say", "can it claim", "allowed to say",
      "allowed to claim", "label as", "market it as", "advertise it as",
      "marketing claim", "advertising claim",
      # Bare "claim" added 2026-08-25 (real gap, RAGAS eval q27): the
      # existing phrases all require the pronoun "it" ("can it claim...")
      # — "can Britannia Brown Bread claim it has as much fibre as an
      # apple" names the product instead of saying "it", so none of them
      # matched, classify_doc_type() returned None, and the real target
      # chunk (a claims_advertising entry) got no boost at all — explains
      # why the original query scored only 0.077 pre-rerank, well below
      # the corrective-retry threshold, before ever reaching a rewrite.
      # "claim" is a closed, stable term for this purpose (see
      # routing/query_router.py's REGULATORY_OVERRIDE_TERMS "claim" entry,
      # added same day for the analogous router-level gap) — safe to add
      # as a bare substring since this is only a soft score boost, never a
      # hard filter (see this list's own docstring above).
      "claim"], "claims_advertising"),
    (["permitted limit", "allowed limit", "compositional standard",
      "fssai limit", "fssai standard", "regulatory limit",
      "permitted level", "legal limit"], "regulatory"),
    (["who guideline", "who recommend", "daily recommended", "healthy diet",
      "recommended intake", "who daily"], "nutrition_general"),
]


def classify_doc_type(query: str) -> str | None:
    q = query.lower()
    for phrases, doc_type in DOC_TYPE_PATTERNS:
        if any(p in q for p in phrases):
            return doc_type
    return None


# Maps an intent label to which of the KB's REAL doc_type values (confirmed
# by grepping data/raw/*.md directly: "ingredient", "ingredient_general",
# "regulatory", "claims_advertising", "nutrition_general" — there is no
# separate "product_nutrition"/"allergen_kb"/"product_catalog" doc_type in
# this KB, those concepts are handled by the SQL-side product_fact route
# and structured/product_comparison.py instead) should be boosted or
# penalized in retrieval/search_hybrid.py. Still soft (a boost/penalty on
# the RRF score), never a hard filter — PHASE3_TESTING_LOG.md Finding 7
# documents a real regression from hard-filtering on this KB's thin/uneven
# doc_type coverage; this strengthens the existing soft mechanism instead
# of repeating that mistake.
#
# STATUS (2026-08-22): kept, but currently unexercised — the keyword-based
# classify_intent() that used to populate the `intent` argument
# (retrieval/search_hybrid.py::search_hybrid()) was retired along with the
# rest of the pre-tool-calling routing layer (see ask_hybrid.py's 2026-08-21
# migration note), and nothing has replaced it as an `intent` source since.
# Every real caller today passes intent=None, so search_hybrid() silently
# falls back to its single-hint classify_doc_type() boost instead — not a
# bug, an explicitly designed fallback (see that function's own docstring).
# This table and the doc_type boost/penalize mechanism it drives are still
# real, working code (not dead in the classify_intent()/_match_*_mention()
# sense — those were deleted outright), just without a current populator;
# left in place as an intentional hook for future work rather than removed,
# since agent/tools.py's fired tool name is a plausible signal to
# reconnect it to.
INTENT_DOC_TYPE_POLICY: dict[str, dict[str, list[str]]] = {
    "nutrition_fact": {"boost": ["nutrition_general"], "penalize": ["regulatory", "claims_advertising"]},
    "nutrition_assessment": {"boost": ["nutrition_general"], "penalize": ["regulatory", "claims_advertising"]},
    "ingredient_question": {"boost": ["ingredient", "ingredient_general"], "penalize": []},
    "allergen_question": {"boost": ["ingredient", "ingredient_general"], "penalize": ["regulatory", "claims_advertising"]},
    "regulatory_question": {"boost": ["regulatory", "claims_advertising"], "penalize": []},
    "compliance_assessment": {"boost": ["regulatory", "claims_advertising", "ingredient"], "penalize": []},
    "health_assessment": {"boost": ["nutrition_general", "ingredient", "ingredient_general"], "penalize": ["claims_advertising"]},
}


@dataclass
class RouteResult:
    route: str                # "product_fact" | "retrieval"
    product_id: str | None    # resolved product, if any (set even on the
                               # retrieval route, for future metadata-scoped
                               # filtering — unused by that route today)
    fact_field: str | None    # nutrition/other fact key, product_fact route only


def _query_tokens(text: str) -> set[str]:
    return set(TOKEN_RE.findall(text.lower()))


def _load_products(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    return conn.execute("SELECT product_id, name, brand FROM products").fetchall()


def find_product(query: str, conn: sqlite3.Connection) -> str | None:
    """
    Resolves which of the 23 catalog products (if any) a query is about.

    Scores each product by how many of its own significant name/brand
    tokens (length >= 3, so "g" in "Parle-G" doesn't count on its own but
    "parle" does) also appear as whole-word tokens in the query. Highest
    score wins; ties or a zero score return None rather than guessing —
    ambiguous product mentions (e.g. two products both branded
    "Coca-Cola") should fall through to retrieval, not a wrong SQL lookup.
    """
    q_tokens = _query_tokens(query)
    if not q_tokens:
        return None

    best_id, best_score = None, 0
    for row in _load_products(conn):
        name_tokens = _query_tokens(row["name"])
        brand_tokens = _query_tokens(row["brand"] or "")
        candidate_tokens = {t for t in (name_tokens | brand_tokens) if len(t) >= 3}
        score = len(candidate_tokens & q_tokens)

        if score > best_score:
            best_id, best_score = row["product_id"], score
        elif score == best_score and score > 0:
            best_id = None  # ambiguous tie — don't guess

    return best_id


def _fuzzy_match_fact_field(query: str) -> str | None:
    """
    Fallback for a single misspelled keyword (e.g. "protien" for
    "protein") — confirmed real 2026-08-20: a real user query with this
    exact typo fell through routing's exact-substring match entirely and
    was answered as "the retrieved documents do not provide the protein
    amount" even though products.sqlite has it. Only checks single-word
    phrases (a multi-word phrase like "total fat" is too ambiguous to
    fuzzy-match word-by-word without risking a false positive) and only
    words of length >= 4, with a cutoff verified against both real typos
    (protien/protein 0.86, sodum/sodium 0.91, cholestrol/cholesterol
    0.95, calorie/calory 0.77 — all pass) and near-miss unrelated words
    (fit/fat 0.67 — correctly rejected) at 0.75.
    """
    q_words = TOKEN_RE.findall(query.lower())
    for phrases, field in NUTRITION_FIELD_PATTERNS + OTHER_FACT_PATTERNS:
        for phrase in phrases:
            if " " in phrase:
                continue
            for w in q_words:
                if len(w) >= 4 and difflib.get_close_matches(w, [phrase], n=1, cutoff=0.75):
                    return field
    return None


def _match_fact_field(query: str) -> str | None:
    q = query.lower()
    for phrases, field in NUTRITION_FIELD_PATTERNS + OTHER_FACT_PATTERNS:
        if any(p in q for p in phrases):
            return field
    return _fuzzy_match_fact_field(query)


def _strip_product_name(query: str, product_id: str, conn: sqlite3.Connection) -> str:
    """
    Removes the resolved product's own name from the query text before
    fact-field/ingredient/allergen matching runs on it.

    Confirmed real gap 2026-08-20: resolve_followup() deliberately
    prepends "For {product_name}: " to a follow-up query so find_product()
    can resolve it (conversation/resolve.py), but that same prepended text
    then also gets scanned by _match_fact_field — for the one product in
    the catalog whose name itself contains a nutrition-field word
    ("Yogabar Daily Protein Bar"), "does this have oats" was wrongly
    matched to protein_g via the product's own name, not the question.
    Stripping the name first (rather than changing resolve_followup, which
    is deliberately tested/tuned elsewhere — see its own docstring) fixes
    this at the actual collision point and also covers a user typing the
    product name directly into a query that separately asks about an
    unrelated field.
    """
    row = conn.execute("SELECT name FROM products WHERE product_id = ?", (product_id,)).fetchone()
    if row is None:
        return query
    return re.sub(re.escape(row["name"]), "", query, flags=re.IGNORECASE)


def classify_query(query: str, conn: sqlite3.Connection) -> RouteResult:
    q = query.lower()
    product_id = find_product(query, conn)

    if (any(term in q for term in REGULATORY_OVERRIDE_TERMS)
            or _COMPOUND_CLAUSE_RE.search(q) or _HEALTH_CONDITION_RE.search(q)):
        return RouteResult(route="retrieval", product_id=product_id, fact_field=None)

    field_match_query = _strip_product_name(query, product_id, conn) if product_id else query

    # A data-driven ingredient/allergen mention matcher (fuzzy-checking the
    # query against the resolved product's own real ingredient/allergen
    # data, not a phrase list) used to run here too, retired 2026-08-21 and
    # deleted outright 2026-08-22 once confirmed fully unreferenced — it
    # fired on any bare mention of a real ingredient/allergen word with no
    # presence-question requirement beyond a definitional-phrase guard,
    # which is exactly the over-eager pattern-matching class of bug this
    # session's tool-calling migration was built to eliminate. Confirmed
    # real: "can I consume it with milk?" (a serving/pairing question) was
    # intercepted here as an allergen check purely because "milk" is a
    # real declared allergen for that product, bypassing the tool-calling
    # loop entirely — including its check_ingredient_or_allergen tool and
    # the system-prompt guidance specifically added to handle this exact
    # pairing-vs-presence distinction, neither of which ever got a chance
    # to run. The tool loop's LLM-level understanding is a strictly better
    # general handler for this now; _match_fact_field (explicit, precise
    # OTHER_FACT_PATTERNS phrases like "allergen"/"contains milk") is kept
    # as the only fast-path field matcher.
    fact_field = _match_fact_field(field_match_query)
    if product_id and fact_field:
        return RouteResult(route="product_fact", product_id=product_id, fact_field=fact_field)

    return RouteResult(route="retrieval", product_id=product_id, fact_field=None)


if __name__ == "__main__":
    from config import get_sqlite_conn

    test_queries = [
        "how many calories are in Parle-G",
        "does McVitie's have two FSSAI license numbers",
        "is aspartame safe in Diet Coke",
        "is Diet Coke's sweetener within the legal limit",
        "what is the exact FSSAI permitted level of DATEM in bread",
    ]
    conn = get_sqlite_conn()
    for q in test_queries:
        result = classify_query(q, conn)
        print(f"{q!r} -> {result}")
    conn.close()
