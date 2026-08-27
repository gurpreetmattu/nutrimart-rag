"""
generation/consistency.py — checks a freshly-generated answer against
ConversationState's known_facts (conversation/state.py), for two real
failure shapes:

1. "Forgotten fact" — the answer claims a known attribute's value is
   unavailable/not specified, when it was already established earlier
   this conversation (a real observed case: told 43g sugar, then later
   says "the retrieved data do not specify sugar amounts").
2. "Numeric contradiction" — the answer states a different number for the
   attribute currently in focus than what's already known.

Complements, does not replace, generation/groundedness.py's
check_groundedness() — that checks a claim against its CITED CHUNK; this
checks a claim against the CONVERSATION's own prior state, a different
source of truth (an answer can be perfectly grounded in a real chunk and
still contradict what this same user was already told two turns ago). Kept
as a separate module for the same reason gateway.py was split out of
llm.py — distinct source of truth, distinct concern.
"""
import re

from generation.groundedness import CHECKED_TAGS, _extract_citations, _split_claims, _NUMERIC_TOKEN_RE

CONTRADICTION_MARKER_TEMPLATE = " ⚠️ [CONTRADICTS EARLIER ANSWER — {reason}]"
# Matches any rendered marker regardless of its {reason} text — used by
# generation/consumer_view.py to strip this technical detail from the
# default consumer-facing view, same as it already strips
# groundedness.py's UNVERIFIED_MARKER.
CONTRADICTION_MARKER_RE = re.compile(r"\s*⚠️ \[CONTRADICTS EARLIER ANSWER — [^\]]*\]")

_UNAVAILABLE_RE = re.compile(
    r"\b(not (?:specif\w*|state\w*|disclos\w*|available|provided|mention\w*)|"
    r"do(?:es)?n'?t (?:specify|state|disclose|provide|mention|have)|"
    r"no (?:information|data) (?:is )?available|"
    r"(?:is|are) unavailable|cannot be determined)\b",
    re.IGNORECASE,
)

# Explicit key -> human word map for known_facts attribute keys, so a
# claim's prose can be checked for whether it plausibly talks about a
# given known attribute at all. Same explicit-mapping style as
# structured/product_facts.py's NUTRITION_LABELS — not derived
# programmatically from the key, deliberately, since e.g. "carb" needs to
# match "carbohydrate_g" and no simple substring rule covers every case
# cleanly.
_ATTRIBUTE_WORDS: dict[str, list[str]] = {
    "total_sugars_g": ["sugar"],
    "added_sugars_g": ["added sugar"],
    "energy_kcal": ["calorie", "energy"],
    "saturated_fat_g": ["saturated fat"],
    "trans_fat_g": ["trans fat"],
    "total_fat_g": ["fat"],
    "protein_g": ["protein"],
    "carbohydrate_g": ["carb"],
    "sodium_mg": ["sodium", "salt"],
    "cholesterol_mg": ["cholesterol"],
}


# Some attributes' trigger words are substrings of a DIFFERENT, more
# specific sibling attribute's own phrasing ("fat" inside "saturated fat"/
# "trans fat"; "sugar" inside "added sugar") — an occurrence immediately
# preceded by one of these words belongs to that sibling, not this
# attribute, and must not be matched here.
_SIBLING_EXCLUSIONS: dict[str, list[str]] = {
    "total_fat_g": ["saturated", "trans", "unsaturated"],
    # "non" catches "non-sugar sweeteners" (nutrition_knowledge_base.md's
    # own WHO NSS terminology) — confirmed real false positive 2026-08-20,
    # same run as the "added sugar" case: the hyphen in "non-sugar" survives
    # a plain rstrip(), so this needs its own explicit entry rather than
    # being caught by a shared "added" exclusion.
    "total_sugars_g": ["added", "non"],
}

_PROXIMITY_WINDOW = 60  # characters either side of an attribute-word mention
_VALUE_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _parse_value(token: str) -> float | None:
    m = _VALUE_RE.match(token)
    return float(m.group()) if m else None


def _attribute_positions(lower_text: str, attribute: str) -> list[int]:
    """
    A LEADING `\\b` word-boundary added 2026-08-25 (real bug, found via a
    live server restart check): a plain substring search for "sodium"
    matches inside "Disodium" (e.g. a cited chunk heading like "Disodium
    5'-Guanylate") — a chemical name fragment, not an actual mention of
    the product's own sodium content. Confirmed real: this produced a
    spurious "sodium_mg was already established..." contradiction flag on
    an answer that never discussed sodium at all.

    Deliberately LEADING-ONLY, not `\\b word \\b` on both sides — several
    of `_ATTRIBUTE_WORDS`'s entries are intentional prefixes of a longer
    real word ("carb" -> "carbohydrate", "sugar" -> "sugars", "calorie" ->
    "calories") and a trailing boundary would break every one of those
    (confirmed directly: `\\bcarb\\b` does NOT match "carbohydrate", nor
    does `\\bsugar\\b` match "sugars"). A leading boundary alone already
    fully fixes the "disodium" case — "sodium" sits mid-word there (`i`
    immediately before `s`, no boundary), so leading-only is both
    sufficient and the narrowest fix that doesn't reintroduce a worse bug.
    """
    exclusions = _SIBLING_EXCLUSIONS.get(attribute, [])
    positions = []
    for word in _ATTRIBUTE_WORDS.get(attribute, []):
        for m in re.finditer(r"\b" + re.escape(word), lower_text):
            # rstrip trailing whitespace AND hyphens — "non-sugar" leaves a
            # bare hyphen directly against "sugar" with no space to strip.
            prefix = lower_text[max(0, m.start() - 20): m.start()].rstrip(" \t-")
            if any(prefix.endswith(ex) for ex in exclusions):
                continue
            positions.append(m.start())
    return positions


def _nearby_same_unit_numbers(block_text: str, positions: list[int], unit_suffix: str) -> set[str]:
    """
    Only pulls numbers physically near an attribute-word mention, not every
    number sharing that unit anywhere in the block. Confirmed real false
    positive 2026-08-20: once get_all_nutrition_facts() started injecting
    a product's full nutrition profile as known_facts at
    once, a single dense summary sentence naming several gram-denominated
    values together (fat, protein, carbs, sugar all share unit "g") made
    every one of those attributes' checks see every other attribute's
    number as a "contradicting" value for itself.
    """
    found = set()
    for m in _NUMERIC_TOKEN_RE.finditer(block_text):
        token = re.sub(r"[\s,]+", "", m.group().lower())
        if not token.endswith(unit_suffix) or token in ("100g", "100ml"):
            continue
        # A number qualified as a per-BODY-WEIGHT or per-DAY rate ("0.8g
        # protein per kilogram of body weight", "50g per day") is a
        # different kind of quantity than the product's own flat
        # per-100g/per-serving fact, even though it shares the same unit
        # suffix — confirmed real false positive 2026-08-21: a WHO/general
        # dosage guideline ("0.8g/kg body weight") got flagged as
        # contradicting the product's own "10.0g protein" known fact
        # purely because both end in "g" and sit near the word "protein".
        # Deliberately does NOT exclude "per 100g"/"per serving" — that IS
        # the same measurement basis known_facts itself uses, excluding
        # those would silently disable real-contradiction detection for
        # the normal case instead of just this one false-positive shape.
        # Searches (not anchors) the tail window — the qualifier typically
        # follows a noun, not the number directly ("0.8g PROTEIN per
        # kilogram of body weight"), confirmed via direct testing.
        tail = block_text[m.end():m.end() + 35].lower()
        if re.search(r"(?:/\s*kg\b|per\s+(?:kg|kilogram)\b|per\s+day\b)", tail):
            continue
        # A guideline/limit word directly AFTER the number ("50g limit",
        # "20g cap", "50 g threshold") is the same threshold-not-fact shape
        # as the head-window check below, just with the marker on the
        # other side — confirmed real 2026-08-26, a second false positive
        # found immediately after the first fix shipped: "(≈94% of a 50g
        # limit)" still flagged 50g as contradicting the product's own
        # 47.4g, because "limit" landed in the TAIL this time, which only
        # the head-window check (below) covered at that point.
        if re.search(r"\b(?:limit|cap|threshold|allowance|ceiling)\b", tail):
            continue
        # A number preceded by a guideline/limit marker ("≤50 g", "under
        # 20g", "no more than 50g", "typical dietary guidelines... (≤50g)")
        # is a THRESHOLD being cited, not a re-assertion of the product's
        # own flat known-fact value — confirmed real false positive
        # 2026-08-26: "Consuming it every day could push you above typical
        # dietary guidelines for added sugars (≤50 g) and saturated fat
        # (≤20 g)" got flagged as contradicting the product's own known
        # added_sugars_g=47.4g, purely because "50g"/"20g" share the same
        # unit and sit near the word "sugar"/"fat" — the same false-
        # positive shape as the per-kg/per-day case above, just with the
        # qualifier BEFORE the number instead of after. Checks a symmetric
        # 35-char window immediately before the match (mirroring `tail`),
        # for either a direct ≤/</<= symbol right against the number or a
        # nearby guideline-language word — deliberately does NOT exclude
        # bare "limit"/"recommend" everywhere in the block (only in this
        # tight pre-number window), so a genuine restated product value
        # that merely appears near unrelated guideline language elsewhere
        # in the same claim still gets checked normally.
        head = block_text[max(0, m.start() - 35):m.start()].lower()
        if re.search(r"[≤≥<>]\s*$", head) or re.search(
            r"(?:no\s+more\s+than|at\s+most|under|below|guideline|recommend\w*|"
            r"should\s+not\s+exceed|upper\s+limit|daily\s+limit)\s*[:\(]?\s*$", head,
        ):
            continue
        if any(abs(m.start() - p) <= _PROXIMITY_WINDOW for p in positions):
            found.add(token)
    return found


def _find_contradiction(block_text: str, known_facts: dict) -> str | None:
    lower = block_text.lower()

    for attribute, fact in known_facts.items():
        positions = _attribute_positions(lower, attribute)
        if not positions:
            continue

        if _UNAVAILABLE_RE.search(block_text):
            return f"{attribute} was already established as {fact['value']}{fact['unit']} earlier in this conversation"

        # Only a claim citing products.sqlite is even capable of
        # re-asserting THIS product's own measured value — a claim citing
        # a KB markdown file (fssai/nutrition/ingredient_knowledge_base.md)
        # is general regulatory/nutrition guidance (e.g. "WHO recommends
        # <50g/day"), which legitimately shares the same attribute word and
        # unit as the product's own fact without being the same
        # measurement at all. Confirmed as a real false positive
        # 2026-08-19 (eval/conversation_questions.py c01 turn 2): a
        # [REGULATORY] claim citing nutrition_knowledge_base.md's WHO
        # 50g/day free-sugar guidance was flagged as "contradicting" the
        # product's own 43g/100g sugar content — two genuinely different
        # facts that happen to share a word and a unit.
        citations = _extract_citations(block_text)
        if citations and not any(source_file == fact["source"] for source_file, _ref in citations):
            continue

        unit_suffix = fact["unit"].lower()
        same_unit_numbers = _nearby_same_unit_numbers(block_text, positions, unit_suffix)
        if not same_unit_numbers:
            continue

        known_value = fact["value"]
        # Numeric comparison, not string equality — confirmed real false
        # positive 2026-08-20: a known fact stored as 0.0 (float) never
        # string-matched the model writing "0g" (no decimal), flagging a
        # correct answer as contradicting itself.
        matches_known = any(
            known_value is not None and (v := _parse_value(n)) is not None and abs(v - float(known_value)) < 1e-9
            for n in same_unit_numbers
        )
        if not matches_known:
            # Plain comma-joined text, not sorted(same_unit_numbers)'s bare
            # str() — that produced a literal Python list repr like
            # "['50g']" embedded in the marker text, which CONTRADICTION_
            # MARKER_RE's own non-nested "[^\]]*" then couldn't strip
            # cleanly (it closed at the list repr's own "]" instead of the
            # marker's real closing bracket), leaking a stray "]" into the
            # consumer-facing answer — confirmed real 2026-08-21.
            numbers_str = ", ".join(sorted(same_unit_numbers))
            return (f"{attribute} was already established as {fact['value']}{fact['unit']}, "
                    f"this claim states {numbers_str}")

    return None


def check_conversation_consistency(answer: str, state: dict) -> str:
    known_facts = (state or {}).get("known_facts") or {}
    if not known_facts:
        return answer

    out_parts = []
    for tag, block_text in _split_claims(answer):
        if tag not in CHECKED_TAGS:
            out_parts.append(block_text)
            continue
        reason = _find_contradiction(block_text, known_facts)
        if reason:
            out_parts.append(block_text.rstrip() + CONTRADICTION_MARKER_TEMPLATE.format(reason=reason))
        else:
            out_parts.append(block_text)

    return "".join(out_parts)
