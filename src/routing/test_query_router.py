"""
routing/test_query_router.py — regression tests for classify_query()'s
deterministic product_fact fast path, focused on the substring-collision
and health-judgment-override bugs found in a 2026-08-28 adversarial pass.

The fast path in classify_query() bypasses the entire tool-calling
loop/LLM synthesis when it fires — so a false positive here doesn't just
mis-tag a route, it silently returns a bare number/fact for a question
that actually needed real judgment (a health-risk verdict, a "-free"
claim-eligibility check, etc.), with zero LLM call to catch the mismatch.
Every case here is a confirmed real bug from that pass, not a
hypothetical: e.g. "will this help me lose weight?" answered with the
product's PACK SIZE (325ml) because a bare "weigh" substring pattern also
matched inside "weight".

No pytest in this project — plain assertions + a __main__ runner, same
convention as every other test_*.py file here. Needs a real SQLite
connection (db/products.sqlite, read-only) to resolve product names —
same requirement classify_query() itself has — but makes no LLM/network
call, so this is still effectively free to run.

Run:
    python src/routing/test_query_router.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import get_sqlite_conn
from routing.query_router import classify_query, find_product

_failures: list[str] = []
_conn = get_sqlite_conn()


def check(label: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        _failures.append(label)


def must_defer(query: str, label: str):
    """route must be 'retrieval' (i.e. NOT silently fast-pathed to a bare fact)."""
    r = classify_query(query, _conn)
    check(f"{label}: {query!r} -> retrieval (was route={r.route!r}, field={r.fact_field!r})",
          r.route == "retrieval")


def must_fast_path(query: str, expected_field: str, label: str):
    """A genuinely simple fact question must still fast-path — regression guard
    against over-broadening the override-term list."""
    r = classify_query(query, _conn)
    check(f"{label}: {query!r} -> product_fact/{expected_field} (was route={r.route!r}, field={r.fact_field!r})",
          r.route == "product_fact" and r.fact_field == expected_field)


# --- Confirmed real bugs: must defer to the tool-calling loop --------------

# The "weigh" substring inside "weight" bug (2026-08-28, live report):
# these two got answered with Yakult's PACK SIZE (325ml), nothing to do
# with what was asked.
must_defer("Will this help me lose weight?", "weight-loss phrasing")
must_defer("Can I eat this if I'm watching my weight?", "weight-loss phrasing")

# "-free" claim-eligibility questions (2026-08-28 audit): fast-pathed to a
# bare nutrition number instead of a real "does this qualify for a 'free'
# claim" verdict.
must_defer("is Kurkure Masala Munch sodium-free?", "-free claim")
must_defer("is Diet Coke caffeine-free?", "-free claim")
must_defer("is Britannia Brown Bread cholesterol-free?", "-free claim")

# "for kids/toddlers/pregnant" + a nutrition keyword (2026-08-28 audit):
# fast-pathed to a bare number instead of a real suitability judgment.
must_defer("is the sugar content in Kurkure Masala Munch ok for kids?", "for-kids phrasing")
must_defer("is the fat content in Britannia Brown Bread suitable for toddlers?", "for-toddlers phrasing")
must_defer("is the caffeine in Diet Coke fine for a pregnant woman?", "pregnant phrasing")

# Health-condition/judgment + a nutrition keyword (2026-08-28 audit).
must_defer("is the caffeine in Diet Coke bad for diabetics?", "diabetic phrasing")
must_defer("will the sugar in Kurkure Masala Munch spike my blood sugar?", "blood-sugar-spike phrasing")
must_defer("is the sodium in Britannia Brown Bread okay for someone with high cholesterol?", "okay-for phrasing")
must_defer("would a doctor recommend the fat content in Britannia Brown Bread?", "recommend phrasing")

# "allergic reaction" fuzzy-matching to the "allergens" field (2026-08-28,
# live report): a RISK question got fast-pathed to a bare allergens dump
# via _fuzzy_match_fact_field()'s typo-tolerance ("allergic" scores above
# its 0.75 cutoff against "allergen"), zero reasoning about actual risk.
must_defer("can Cadbury Dairy Milk Chocolate Bar cause an allergic reaction?", "allergic-reaction phrasing")

# Quantity-multiplier questions (2026-08-28, live report): the SQL fast
# path can only ever return the raw stored per-serving value — it can't
# compute "3 packets worth" — so these must always defer to the
# tool-calling loop's [DERIVED CALCULATION] capability instead of silently
# answering with a misleadingly incomplete number.
must_defer("if I eat 3 packets of Kurkure Masala Munch how much sodium is that", "quantity-multiplier phrasing")
must_defer("how many packets of Parle-G equal 2000 calories", "quantity-multiplier phrasing")

# --- Regression guard: plain fact lookups must still fast-path -------------
# (verifies the override-term additions above didn't over-broaden into
# deferring ordinary questions — "cholesterol" bare was tried and reverted
# for exactly this reason during this fix.)
must_fast_path("how much sodium is in Britannia Brown Bread", "sodium_mg", "plain fact")
must_fast_path("what is the cholesterol content of Amul Dark Chocolate", "cholesterol_mg", "plain fact")
must_fast_path("how much caffeine is in Diet Coke", "caffeine_mg", "plain fact")
must_fast_path("what is the fat content of Kurkure Masala Munch", "total_fat_g", "plain fact")
must_fast_path("what is the pack size of Yakult Probiotic Drink", "pack_size", "plain fact")
must_fast_path("who makes McVitie's Digestive", "brand", "plain fact")
must_fast_path("how many calories are in Parle-G", "energy_kcal", "plain fact")
must_fast_path("does Cadbury Dairy Milk Chocolate Bar contain any allergens?", "allergens", "plain fact")


# --- find_product(): generic marketing-name-word collisions -------------
# Confirmed real (2026-08-28, follow-up to the audit above): several
# catalog products carry ordinary English words inside their own marketing
# name ("Britannia GOOD DAY Cashew Cookies", "...No MAIDA", "Yogabar Daily
# PROTEIN Bar", "McVitie's Digestive High FIBRE Biscuits"). A single such
# word matching was previously enough to silently resolve a completely
# unrelated, product-agnostic question to that one product — and that
# wrong product_id then gets written into conversation state, silently
# scoping every later follow-up too. Fixed: a name-only word (not also a
# brand token) now needs 2+ independent matches to count.
def must_not_resolve(query: str, label: str):
    pid = find_product(query, _conn)
    check(f"{label}: {query!r} -> no product resolved (was {pid!r})", pid is None)


must_not_resolve("is sugar good for health", "generic 'good' collision (Good Day Cashew Cookies)")
must_not_resolve("what is maida?", "generic 'maida' collision (Kellogg's Chocos)")
must_not_resolve("what is protein", "generic 'protein' collision (Yogabar Protein Bar)")
must_not_resolve("what is fibre", "generic 'fibre' collision (McVitie's Digestive)")

# Regression guard: a real single-word BRAND mention (the ordinary,
# legitimate way users name a product) must still resolve.
def must_resolve(query: str, expected_pid: str, label: str):
    pid = find_product(query, _conn)
    check(f"{label}: {query!r} -> {expected_pid} (was {pid!r})", pid == expected_pid)


must_resolve("how much sodium is in Kurkure", "kurkure_masala_munch", "single-word brand mention")
must_resolve("tell me about Yakult", "yakult_probiotic_drink", "single-word brand mention")
must_resolve("how many calories in Parle-G", "parle_g_original", "single-word brand mention")


if __name__ == "__main__":
    _conn.close()
    print(f"\n{len(_failures)} failure(s)." if _failures else "\nAll query_router regression checks passed.")
    sys.exit(1 if _failures else 0)
