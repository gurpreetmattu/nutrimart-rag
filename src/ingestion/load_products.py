"""
load_products.py — loads products_compiled.json into SQLite.

This is the structured store — product-fact queries (Phase 5 step 2 of the
pipeline) hit this directly via SQL, bypassing retrieval entirely. Nested
fields (ingredients_parsed, nutrition, allergens, fortification) are stored
as JSON text columns and queried with SQLite's json_extract() rather than
being normalized into separate tables — the product count (23) is small
enough that normalization would add complexity without a real query-speed
benefit.
"""
import json
import sqlite3
from pathlib import Path


SCHEMA = """
CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    pack_size_json TEXT,             -- JSON: {value, unit}
    ingredients_raw TEXT,
    ingredients_parsed_json TEXT,   -- JSON array of {name, component}
    allergens_contains_json TEXT,   -- JSON array
    allergens_may_contain_json TEXT,-- JSON array
    allergen_declaration_present INTEGER,
    nutrition_json TEXT,            -- full nutrition object as JSON
    fortification_json TEXT,        -- JSON, may be null
    description TEXT,
    source_url TEXT,
    fssai_license TEXT,
    co_licensee_fssai TEXT,
    data_note TEXT
);
"""


def load_products(json_path: Path, db_path: Path) -> int:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    products = data["products"]

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    cur.execute("DELETE FROM products")  # idempotent re-run

    for p in products:
        nutrition = p.get("nutrition", {})
        cur.execute(
            """
            INSERT INTO products (
                product_id, name, brand, category, pack_size_json,
                ingredients_raw, ingredients_parsed_json,
                allergens_contains_json, allergens_may_contain_json,
                allergen_declaration_present, nutrition_json,
                fortification_json, description, source_url,
                fssai_license, co_licensee_fssai, data_note
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                p.get("product_id"),
                p.get("name"),
                p.get("brand"),
                p.get("category"),
                json.dumps(p.get("pack_size")) if p.get("pack_size") else None,
                p.get("ingredients_raw"),
                json.dumps(p.get("ingredients_parsed", [])),
                json.dumps(p.get("allergens_contains", [])),
                json.dumps(p.get("allergens_may_contain", [])),
                int(bool(p.get("allergen_declaration_present"))),
                json.dumps(nutrition),
                json.dumps(p.get("fortification")) if p.get("fortification") else None,
                p.get("description"),
                p.get("source_url"),
                p.get("fssai_license"),
                p.get("co_licensee_fssai"),
                p.get("data_note"),
            ),
        )

    conn.commit()
    count = cur.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    conn.close()
    return count


if __name__ == "__main__":
    import sys
    raw_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("data/raw")
    db_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("db")

    n = load_products(raw_dir / "products_compiled.json", db_dir / "products.sqlite")
    print(f"Loaded {n} products into {db_dir / 'products.sqlite'}")

    # Quick sanity query
    conn = sqlite3.connect(db_dir / "products.sqlite")
    row = conn.execute(
        "SELECT name, json_extract(nutrition_json, '$.basis'), "
        "json_extract(pack_size_json, '$.value'), json_extract(pack_size_json, '$.unit') "
        "FROM products LIMIT 1"
    ).fetchone()
    print(f"Sanity check — first product: {row}")
    conn.close()
