"""
product_ingredients.py — extracts a product's INS-style additive codes
from products.sqlite, for the hybrid pipeline's ingredient-entity
retrieval scoping (see retrieval/search_hybrid.py).

products_compiled.json's ingredients_parsed names embed INS codes as a
plain suffix in the ingredient's free-text name (e.g. "colour 160c",
"acidity regulator 334", "raising agent 503(ii)", "emulsifier 472e") —
there's no separate structured INS-code field to read directly. The
regex below pulls the code back out. Verified directly against real data:
Kurkure's parsed ingredients include "colour 160c" and "acidity regulator
334" but nothing resembling INS 476 (PGPR) — confirming a real bug where
PGPR had been surfacing as irrelevant noise for a Kurkure query.
"""
import json
import re
import sqlite3

# Matches an INS-style code embedded in an ingredient name: 3-4 digits,
# optionally followed by a lowercase letter suffix (e.g. "472e", "160c")
# and/or a parenthetical roman/latin sub-index (e.g. "(ii)", "(i)").
INS_CODE_RE = re.compile(r"\b(\d{3,4}[a-z]{0,3}(?:\([a-z]+\))?)")


def get_product_ins_codes(product_id: str, conn: sqlite3.Connection) -> set[str]:
    row = conn.execute(
        "SELECT ingredients_parsed_json FROM products WHERE product_id = ?",
        (product_id,),
    ).fetchone()
    if row is None:
        return set()

    ingredients = json.loads(row["ingredients_parsed_json"] or "[]")
    codes: set[str] = set()
    for ing in ingredients:
        name = (ing.get("name") or "").lower()
        codes.update(INS_CODE_RE.findall(name))
    return codes


if __name__ == "__main__":
    import sys
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent.parent))
    from config import get_sqlite_conn

    product_id = sys.argv[1] if len(sys.argv) > 1 else "kurkure_masala_munch"
    conn = get_sqlite_conn()
    codes = get_product_ins_codes(product_id, conn)
    print(f"{product_id} -> {sorted(codes)}")
    conn.close()
