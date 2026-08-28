"""
conversation/resolve.py — expands a short follow-up question into a
self-contained query before it ever reaches routing/retrieval: "before
searching the knowledge base, convert short follow-up questions into a
fully understood internal query."

Template-based, not an LLM call — this needs to keep working even when
every configured LLM provider is exhausted (a real, current constraint
this project hits regularly), and a fixed template is easy to reason
about correctness for.

**Phrasing DOES matter here, verified empirically 2026-08-19** — an
earlier assumption that any phrasing containing the right
product/attribute/value would do turned out to be wrong. Real test:
resolving "is that too much?" to `"For Amul Dark Chocolate: is that too
much (referring to: total_sugars_g = 43.0g...)"` — product name leading,
fact trailing — retrieved PGPR/lecithin ingredient chunks at rerank score
0.62 while the one relevant nutrition-guidance chunk in the pool scored
0.0007, a ~900x gap retrieval/search_hybrid.py's intent-based doc_type
boost (a modest RRF nudge) cannot bridge and should not be force-bridged
(an artificially huge boost would just misfire on unrelated queries).
Root cause: the product-name-heavy phrasing shares vocabulary with
product/ingredient chunks specifically, dragging the cross-encoder toward
them regardless of which doc_types even reach the pool. Fixed by leading
with the concrete fact/value instead ("Is 43 g of total sugar per 100 g
... a high amount?", value first) — re-verified this retrieves the actual
relevant nutrition-guidance content instead.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from structured.product_facts import NUTRITION_LABELS
from routing.query_router import _match_fact_field

_ANAPHORA_RE = re.compile(r"\b(this|that|it|these|those)\b", re.IGNORECASE)
_SHORT_QUERY_WORD_LIMIT = 8

# Catches "how much/many <noun>" so _names_other_fact_field can recognize a
# query is naming a DIFFERENT attribute even when that attribute has no
# NUTRITION_FIELD_PATTERNS entry at all (e.g. "fibre" — not a tracked
# nutrition field, a documented schema gap, see test_questions.py q20).
_QUANTITY_NOUN_RE = re.compile(r"\bhow (?:much|many)\s+([a-z]+)", re.IGNORECASE)
_QUANTITY_STOPWORDS = {"is", "are", "was", "were", "does", "do", "did", "of", "the", "a", "an", "in", "there", "for"}

# Ingredient/allergen-presence phrasing ("does it have X", "is there any X
# in it", "does this contain X") — never about the active NUMERIC
# attribute, so the attribute-anaphora rewrite must not fire for these
# either, same reasoning as the quantity-noun heuristic above. Confirmed
# real 2026-08-21: without this, "does it have any casew nuts in it" (with
# active_attribute=total_sugars_g from an earlier turn) got rewritten to
# "Is 20.5g of total sugars a lot? does it have any casew nuts in it" — a
# nonsensical merged query that confused the tool-calling model into
# calling no tool at all rather than check_ingredient_or_allergen.
_INGREDIENT_PRESENCE_RE = re.compile(
    r"\b(?:have|has|contain|contains|any)\b.{0,20}\b(?:in it|in this|in that)\b"
    r"|\b(?:does|is there)\b.{0,20}\b(?:have|contain|any)\b",
    re.IGNORECASE,
)

# Positive allowlist for the attribute-anaphora rewrite (2026-08-21, replaces
# the previous "fire unless blocklisted" default). Confirmed real via live
# browser testing: "how to eat this bread?" and "is this good breakfast
# choice?" both slipped past every blocklist check above (no "how much/many"
# pattern, no ingredient-presence pattern) and still got rewritten to lead
# with a stale unrelated numeric fact from an earlier turn ("Is 0g of Trans
# Fat a lot? how to eat this bread?"), which the fast path then confidently
# (and wrongly) answered with the old trans-fat value. A blocklist can only
# ever cover phrasings someone already thought to test — the exact,
# repeatedly-relearned lesson of this whole session (see agent/tools.py's
# module docstring). This module deliberately stays template-based (see
# module docstring — must keep working with both LLM providers down), so the
# fix here is a narrow, high-precision ALLOWLIST instead: only rewrite when
# the query is unambiguously asking to judge the ACTIVE VALUE itself ("is
# that too much", "is it a lot", "how much is that"), not for any other
# anaphoric short question.
_VALUE_JUDGMENT_RE = re.compile(
    r"\b(?:is|was|are)\s+(?:that|it|this|these|those)\b(?:\s+\w+){0,3}?\s+"
    r"(?:too much|too many|too high|too low|a lot|excessive|significant|"
    r"okay|ok|fine|normal|safe|acceptable|high|low)\b"
    r"|\bhow much is (?:that|it|this)\b",
    re.IGNORECASE,
)

# Bare "what is/are X" definitional question with NO anaphoric reference to
# the active product ("this"/"it"/etc — those are still genuinely about the
# product, e.g. "what is this ingredient"). Confirmed real, live
# (2026-08-28): with Britannia Brown Bread active, "what is maida?" got
# rewritten to "For Britannia Brown Bread: what is maida?" — same root
# cause the module docstring above already documents for the value-judgment
# case (product-name-heavy phrasing drags the cross-encoder toward that
# product's own ingredient/additive chunks), just never extended to this
# second, unconditional prepend branch. Live result: retrieval returned
# Brown Bread's own INS-coded additive chunks (Ammonium Chloride, DATEM,
# Calcium Propionate) instead of ingredient_kb_tier2.md's actual "Refined
# wheat flour (maida)" entry, and the answer wrongly claimed maida "isn't
# defined" in the retrieved context — a real KB entry existed the whole
# time, generic-definition retrieval just never reached it.
_BARE_DEFINITIONAL_RE = re.compile(r"^\s*what\s+(?:is|are)\s+(?:a|an|the)?\s*\S", re.IGNORECASE)


def _attribute_label(attribute: str) -> str:
    label, _unit = NUTRITION_LABELS.get(attribute, (attribute.replace("_g", "").replace("_mg", "").replace("_", " "), ""))
    return label


def _names_other_fact_field(query: str, active_attr: str | None) -> bool:
    """
    True if `query` itself names a fact field different from the one
    currently in focus — e.g. "how much protein is there in this?" while
    active_attribute is still total_sugars_g from an earlier turn.

    Confirmed real 2026-08-20: without this check, resolve_followup's
    attribute-anaphora branch fired on ANY short query containing "this"/
    "it", regardless of what it was actually asking about — a follow-up
    about protein got rewritten to lead with the *old* sugar fact ("Is
    43.0g of Total Sugars a lot? how much protein is there in this?"),
    which both misroutes (product_fact never sees a protein fact_field
    match) and drags retrieval toward sugar content instead of protein.
    "this"/"it" here refers to the PRODUCT, not the previously-discussed
    value, whenever the query names its own attribute.
    """
    field = _match_fact_field(query)
    if field is not None:
        return field != active_attr

    # field is None: the query might still be naming a real attribute that
    # just isn't in NUTRITION_FIELD_PATTERNS/OTHER_FACT_PATTERNS (a known
    # coverage gap, not "no attribute mentioned"). Confirmed real
    # 2026-08-21 (conversation_eval.md c02 turn 6): without this,
    # "how much fibre is in this" fell through as if still about the OLD
    # active attribute (total_sugars_g), so the anaphora rewrite below led
    # with "Is 17.6g of Total Sugars a lot?" and the fast path then
    # confidently answered with sugars instead of fibre — a materially
    # worse failure than the known "falls through to retrieval" gap this
    # was supposed to produce. Heuristic: a "how much/many <noun>" query
    # whose <noun> isn't a stopword/anaphor and doesn't overlap with the
    # active attribute's own label names something else, even if we can't
    # say what field it is — "how much is that" (noun="is", a stopword)
    # is left alone and still treated as a same-attribute continuation.
    if not active_attr:
        return False
    if _INGREDIENT_PRESENCE_RE.search(query):
        return True
    m = _QUANTITY_NOUN_RE.search(query)
    if not m:
        return False
    noun = m.group(1).lower()
    if noun in _QUANTITY_STOPWORDS or _ANAPHORA_RE.match(noun):
        return False
    label_words = set(_attribute_label(active_attr).lower().split())
    return noun not in label_words


def resolve_followup(query: str, state: dict) -> str:
    """
    Two expansions, mutually exclusive (a fact-led rewrite already implies
    the product, so it doesn't also get the plain product prefix below):

    1. Attribute/value context: if the query is short and uses an
       anaphoric reference ("is THIS too much?") and a specific fact is
       currently in focus (state["active_attribute"]), rewrite the query
       to LEAD with that concrete fact — "Is {value}{unit} of {label} in
       {product} a lot? {original query}" — rather than appending it as a
       trailing aside. See the module docstring for why leading with the
       fact (not the product name) is the verified-better phrasing.
    2. Otherwise, if the query doesn't already name the active product and
       one is known, prepend it — subsumes what
       api/main.py::_contextualize_query used to do on its own (that
       function's UI-context-only signal is now folded into `state`
       before this is called, see api/main.py's wiring).
    """
    product_name = state.get("product_name")
    product_id = state.get("product_id")

    is_short = len(query.split()) <= _SHORT_QUERY_WORD_LIMIT
    has_anaphora = bool(_ANAPHORA_RE.search(query))
    active_attr = state.get("active_attribute")
    fact = state.get("known_facts", {}).get(active_attr) if active_attr else None

    if (is_short and has_anaphora and fact is not None
            and _VALUE_JUDGMENT_RE.search(query)
            and not _names_other_fact_field(query, active_attr)):
        # Deliberately NOT "...in {product_name}" — verified this drags
        # the cross-encoder toward product/ingredient-specific chunks
        # over generic guidance chunks (same root cause as the module
        # docstring's finding, one layer further). Product continuity
        # across turns is handled structurally instead — the pipeline
        # falls back to conversation_state's remembered product_id when
        # this text-only routing can't resolve one, rather than
        # re-mentioning the name in every follow-up's text.
        label = _attribute_label(active_attr)
        return f"Is {fact['value']}{fact['unit']} of {label} a lot? {query}"

    if product_id and product_name and product_name.lower() not in query.lower():
        # A bare "what is X" definitional question with no anaphora and no
        # recognized product-fact-field match is asking what something IS
        # in general, not about this specific product's own data — leave it
        # unresolved (see _BARE_DEFINITIONAL_RE's docstring above) rather
        # than dragging retrieval toward the active product's own chunks.
        # effective_product_id still falls back to conversation_state
        # downstream if the tool-calling loop genuinely needs it (e.g. it
        # decides to also check whether THIS product contains that
        # ingredient) — only the QUERY TEXT is left product-name-free here.
        if (_BARE_DEFINITIONAL_RE.match(query) and not _ANAPHORA_RE.search(query)
                and _match_fact_field(query) is None):
            return query
        return f"For {product_name}: {query}"

    return query
