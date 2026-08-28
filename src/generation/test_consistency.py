"""
generation/test_consistency.py — regression tests for consistency.py's
known_facts contradiction-detection logic, covering both this session's new
fix (Finding 41: a guideline/limit number like "≤50g" wrongly flagged as
contradicting the product's own known value) and the pre-existing
documented false-positive fixes this same function already carries
(per-kg/per-day rate exclusion; the Finding-32 "Disodium" word-boundary
fix), so a future change to this logic can't silently regress any of them.

No pytest in this project — plain assertions + a __main__ runner, same
convention as api/test_security.py and generation/test_token_budget.py.
Entirely offline — no LLM/network call, this module has none to make.

Run:
    python src/generation/test_consistency.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Test labels below quote real "≤" characters from the actual bug reports —
# reconfigure stdout so this runs cleanly on a default Windows console
# (cp1252), which otherwise crashes on the first non-ASCII print.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from generation.consistency import check_conversation_consistency

_failures: list[str] = []


def check(label: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        _failures.append(label)


def _state(attr: str, value: float, unit: str = "g", source: str = "products.sqlite") -> dict:
    return {"known_facts": {attr: {"value": value, "unit": unit, "source": source}}}


# --- Finding 41: guideline/limit numbers ("≤50g") must not be treated as --
# --- re-assertions of the product's own known value -----------------------

state = _state("added_sugars_g", 47.4)
guideline_answer = ("[INTERPRETATION] Consuming it every day could push you above typical dietary "
                     "guidelines for added sugars (≤50 g) and saturated fat (≤20 g).")
result = check_conversation_consistency(guideline_answer, state)
check("a '≤' guideline-limit number does not false-positive against the product's own known value",
      "CONTRADICTS" not in result)
check("the guideline-limit answer text is returned completely unchanged", result == guideline_answer)

no_more_than_answer = "[INTERPRETATION] Daily intake should stay under 50g to meet WHO's no more than 50g guidance."
check("'no more than 50g' guideline phrasing does not false-positive",
      "CONTRADICTS" not in check_conversation_consistency(no_more_than_answer, state))

# Second false positive found immediately after the first fix shipped: the
# guideline marker can land in the TAIL instead of the head ("50g limit",
# not "limit ... 50g") — confirmed real 2026-08-26 via live re-testing.
tail_limit_answer = ("[INTERPRETATION] Consuming it every day would contribute a large share of the "
                      "recommended daily limits for added sugars (≈94 % of a 50 g limit) and "
                      "saturated fat (≈98 % of a 20 g limit).")
check("a guideline number followed by 'limit' (marker AFTER the number) does not false-positive",
      "CONTRADICTS" not in check_conversation_consistency(tail_limit_answer, state))

# --- Pre-existing false-positive fixes, re-verified not to have regressed -

per_kg_answer = "[REGULATORY] WHO recommends 0.8g protein per kilogram of body weight daily."
check("the pre-existing per-kg-body-weight exclusion still works",
      "CONTRADICTS" not in check_conversation_consistency(per_kg_answer, _state("protein_g", 10.0)))

per_day_answer = "[REGULATORY] WHO recommends limiting free sugar intake to 50g per day."
check("the pre-existing per-day-rate exclusion still works",
      "CONTRADICTS" not in check_conversation_consistency(per_day_answer, _state("total_sugars_g", 43.0)))

disodium_answer = ("[FACT] The flavour enhancer is Disodium 5'-Guanylate / Disodium 5'-Inosinate, "
                    "ADI not specified (ingredient_knowledge_base.md).")
check("the Finding-32 'Disodium' substring-match fix still works (no false 'sodium' flag)",
      "CONTRADICTS" not in check_conversation_consistency(disodium_answer, _state("sodium_mg", 1247.1, unit="mg")))

# --- Real detection must still fire (this fix must not over-correct) ------

wrong_value_answer = "[FACT] This product has 50g of added sugars (products.sqlite)."
check("a genuine restated WRONG value still gets flagged",
      "CONTRADICTS" in check_conversation_consistency(wrong_value_answer, state))

correct_value_answer = "[FACT] This product has 47.4g of added sugars (products.sqlite)."
check("a genuine restated CORRECT value is not flagged",
      "CONTRADICTS" not in check_conversation_consistency(correct_value_answer, state))

# [FACT]-tagged, not [UNCERTAIN] — CHECKED_TAGS (groundedness.py) only
# checks FACT/REGULATORY/INTERPRETATION blocks, deliberately skipping
# UNCERTAIN ones (an uncertain claim isn't asserting a fact to contradict).
forgotten_fact_answer = "[FACT] The retrieved data does not specify the added sugars amount."
check("a genuine 'forgotten fact' case still gets flagged",
      "CONTRADICTS" in check_conversation_consistency(forgotten_fact_answer, state))

# --- Sibling-attribute false positive (2026-08-28, live report) -----------
# "the low total fat (1.5 g) and zero trans fat contribute to..." flagged
# 1.5g as contradicting trans_fat_g=0g purely because it sits within the
# proximity window of the word "trans fat", even though it's textually
# attached to "total fat" right next to it.

sibling_answer = ("[FACT] The low total fat (1.5 g) and zero trans fat contribute to a modest "
                   "calorie profile of 246 kcal.")
check("a number tightly attached to a SIBLING attribute (total fat) does not "
      "false-positive against a different attribute (trans fat) mentioned nearby",
      "CONTRADICTS" not in check_conversation_consistency(sibling_answer, _state("trans_fat_g", 0.0)))

# The sibling fix must not blind total_fat_g to its OWN correct value in the
# same sentence.
check("the sibling fix doesn't blind total_fat_g to its own correct value in the same sentence",
      "CONTRADICTS" not in check_conversation_consistency(sibling_answer, _state("total_fat_g", 1.5)))

# A genuinely WRONG total_fat_g value in the same sentence shape must still
# be caught — the sibling fix must not over-correct into silence.
wrong_sibling_answer = ("[FACT] The low total fat (3.0 g) and zero trans fat contribute to a modest "
                         "calorie profile of 246 kcal.")
check("a genuine wrong value for total_fat_g in the same sentence shape still gets flagged",
      "CONTRADICTS" in check_conversation_consistency(wrong_sibling_answer, _state("total_fat_g", 1.5)))

# A genuine contradiction for trans_fat_g itself (not a sibling mix-up) must
# still be caught.
trans_fat_wrong_answer = "[FACT] This product has 2.0 g of trans fat."
check("a genuine wrong value for trans_fat_g itself still gets flagged",
      "CONTRADICTS" in check_conversation_consistency(trans_fat_wrong_answer, _state("trans_fat_g", 0.0)))

# --- No known_facts at all: always a no-op ---------------------------------

check("no known_facts means the answer passes through completely unchanged",
      check_conversation_consistency("[FACT] Anything at all.", {}) == "[FACT] Anything at all.")

print()
if _failures:
    print(f"{len(_failures)} FAILURE(S):")
    for f in _failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All consistency regression checks passed.")
