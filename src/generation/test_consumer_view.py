"""
generation/test_consumer_view.py — regression tests for
consumer_view.py::to_consumer_friendly(), the regex stripper that hides
typed-claim tags and citations from the default consumer-facing answer.

Added 2026-08-28 after a live deployment leaked two internal-filename
citation shapes straight into the user-facing chat bubble: a bare
"(ingredient_knowledge_base.md)" with no chunk/heading ref (the existing
stripper only recognized "(file, ref)" with a comma), and
"(all from products.sqlite)" (the existing products.sqlite stripper only
matched when the parenthetical STARTED with that literal, so wording in
front of it defeated the match). Both fixed by generalizing into one
regex that strips any parenthetical CONTAINING an internal filename
literal, anywhere inside it.

No pytest in this project — plain assertions + a __main__ runner, same
convention as every other test_*.py file here. Pure regex checks: no LLM
call, no Qdrant, no quota cost.

Run:
    python src/generation/test_consumer_view.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generation.consumer_view import to_consumer_friendly

_failures: list[str] = []


def check(label: str, condition: bool):
    status = "PASS" if condition else "FAIL"
    print(f"[{status}] {label}")
    if not condition:
        _failures.append(label)


def not_leaked(text: str, forbidden: str, label: str):
    result = to_consumer_friendly(text)
    check(f"{label} (got: {result!r})", forbidden not in result)


# --- Confirmed real leaks, both from the same live deployed answer ---------
not_leaked(
    "[FACT] Key additives include DATEM (GMP for bread) (ingredient_knowledge_base.md).",
    "ingredient_knowledge_base.md",
    "bare KB filename citation with no chunk ref",
)
not_leaked(
    "[FACT] Protein: 7.9 g; total sugars: 1.9 g (all from products.sqlite).",
    "products.sqlite",
    "filename embedded mid-phrase, not a strict prefix",
)

# --- Other malformed-citation shapes already handled, still covered here ---
not_leaked(
    "[FACT] Contains milk (products.sqlite, product_id).",
    "products.sqlite",
    "proper products.sqlite citation with ref",
)
not_leaked(
    "[UNCERTAIN] Not confirmed (Source 2: fssai_knowledge_base.md, Chunk 37).",
    "Source 2",
    "internal Source-N prompt label leaking",
)
not_leaked(
    "[FACT] BHA is permitted up to 0.005% (fssai_knowledge_base.md, Chunk 4).",
    "fssai_knowledge_base.md",
    "well-formed file+ref citation",
)

# --- Tag stripping still works -----------------------------------------
result = to_consumer_friendly("[FACT] BHA is permitted up to 0.005% (fssai_knowledge_base.md, Chunk 4).")
check(f"[TAG] prefix stripped (got: {result!r})", not result.startswith("[FACT]"))

# --- False-positive guard: a legitimate parenthetical must survive ---------
result = to_consumer_friendly("[FACT] Sodium is 542mg (INS 150c).")
check(f"legitimate parenthetical (INS 150c) survives (got: {result!r})", "(INS 150c)" in result)

result = to_consumer_friendly(
    "[FACT] Key additives include ammonium chloride (GMP-blanket list), "
    "sorbic acid (up to 1,000 mg/kg for bakery)."
)
check(f"legitimate technical asides survive (got: {result!r})",
      "(GMP-blanket list)" in result and "(up to 1,000 mg/kg for bakery)" in result)


if __name__ == "__main__":
    print(f"\n{len(_failures)} failure(s)." if _failures else "\nAll consumer_view regression checks passed.")
    sys.exit(1 if _failures else 0)
