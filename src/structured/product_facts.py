"""
product_facts.py — direct SQL lookup + deterministic formatting for
product-fact queries, routed here by routing/query_router.py.

Per project_state_summary.md's pipeline design: "Product-fact queries ->
direct SQL lookup + code-computed derivations. Bypasses RAG entirely."
No LLM call in this path — the answer is built straight from the
database row, since the value is already a known fact, not something
that needs retrieval or synthesis. It's still typed [FACT] and cited to
the DB, matching the claim-typing contract the LLM path uses in
generation/llm.py.
"""
import json
import re
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from routing.query_router import NUTRITION_FIELD_PATTERNS
from structured.product_ingredients import INS_CODE_RE

_INS_NAME_INDEX: dict[str, list[str]] | None = None


def _get_ins_name_index() -> dict[str, list[str]]:
    """
    Maps a real INS code (e.g. "223") to the common/chemical name(s) the
    KB actually knows it by (e.g. ["sodium metabisulphite"]) — built once
    from `ingestion/parse_kb.py::parse_all_kb_files()`, the SAME parser
    `retrieval/bm25_index.py` already uses, not a second hand-typed
    synonym list (this project has repeatedly hit bugs from exactly that
    class of drift-prone duplication — see routing/query_router.py's own
    history). Pure markdown parsing, no Qdrant/embedding-model cost, so
    this stays cheap enough for `check_ingredient_or_allergen`'s "instant"
    contract.

    Added 2026-08-24 after a confirmed real wrong answer: McVitie's
    Digestive declares "Dough Conditioner (INS 223)" — the functional-
    class name on the label — but a user/LLM asking about "sulphite" (the
    actual chemical it is) got "not found," because the old fuzzy match
    only ever compared against the label's own functional-class text,
    which never mentions the chemical name at all. Any additive declared
    by function+INS-number (raising agents, emulsifiers, dough
    conditioners, anticaking agents, ...) was invisible to a query using
    its real name.
    """
    global _INS_NAME_INDEX
    if _INS_NAME_INDEX is not None:
        return _INS_NAME_INDEX

    from ingestion.parse_kb import parse_all_kb_files

    index: dict[str, list[str]] = {}
    for chunk in parse_all_kb_files(Path("data/raw")):
        if not chunk.ins_no or not chunk.entity:
            continue
        # entity looks like "Sodium Metabisulphite (INS 223)" — strip the
        # trailing "(INS ...)" to get the plain common name.
        common_name = re.sub(r"\s*\(INS[^)]*\)\s*$", "", chunk.entity, flags=re.IGNORECASE).strip().lower()
        if not common_name:
            continue
        # ins_no can list several codes for one entry, e.g. "627/631/635"
        # or "450(i), 451(i), 452(i)" — each still needs its own key so a
        # product declaring just one of them still matches.
        for code in re.split(r"[,/]", chunk.ins_no):
            code = code.strip()
            if not code:
                continue
            names = index.setdefault(code, [])
            if common_name not in names:
                names.append(common_name)

    _INS_NAME_INDEX = index
    return index


NUTRITION_FIELDS = {field for _, field in NUTRITION_FIELD_PATTERNS}

# nutrition.values key -> (human label, unit)
NUTRITION_LABELS = {
    "energy_kcal": ("energy", "kcal"),
    "protein_g": ("protein", "g"),
    "carbohydrate_g": ("carbohydrate", "g"),
    "total_sugars_g": ("total sugars", "g"),
    "added_sugars_g": ("added sugars", "g"),
    "total_fat_g": ("total fat", "g"),
    "saturated_fat_g": ("saturated fat", "g"),
    "trans_fat_g": ("trans fat", "g"),
    "cholesterol_mg": ("cholesterol", "mg"),
    "sodium_mg": ("sodium", "mg"),
    "dietary_fibre_g": ("dietary fibre", "g"),
    # Added 2026-08-22 (systematic audit, same class of gap as
    # dietary_fibre_g): these 9 fields genuinely exist in nutrition_json
    # for at least one catalog product but were never wired into
    # NUTRITION_LABELS/NUTRITION_FIELD_PATTERNS. caffeine_mg specifically
    # confirmed this bug's real cost: Diet Coke's caffeine question was
    # being answered via a regex-extracted quantity from ingredients_raw
    # text (a workaround built 2026-08-22 for the same conversation) when
    # a proper, direct nutrition_json field (caffeine_mg=10) was sitting
    # there the whole time. Deliberately does NOT include the 4 other
    # untracked keys found in the same audit — saturated_fat_g_not_more_than,
    # saturated_fat_g_palmolein_batch, saturated_fat_g_rice_bran_oil_batch,
    # trans_fat_g_not_more_than — those are ceiling/batch-conditional
    # values (matches products_compiled.json's own documented
    # "batch-dependent nutrition for Lay's" schema_notes), not a plain
    # measured amount; adding them as ordinary fields would let the model
    # present an approximate/conditional number as if it were a definite
    # fact, which is a worse failure mode than the current gap.
    "caffeine_mg": ("caffeine", "mg"),
    "calcium_mg": ("calcium", "mg"),
    "iron_mg": ("iron", "mg"),
    "potassium_mg": ("potassium", "mg"),
    "vitamin_c_mg": ("vitamin C", "mg"),
    "mono_unsaturated_fat_g": ("monounsaturated fat", "g"),
    "poly_unsaturated_fat_g": ("polyunsaturated fat", "g"),
    "energy_from_fat_kcal": ("energy from fat", "kcal"),
    "total_salt_g": ("total salt", "g"),
}


def get_product_row(product_id: str, conn: sqlite3.Connection) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM products WHERE product_id = ?", (product_id,)
    ).fetchone()


def get_all_nutrition_facts(product_id: str, conn: sqlite3.Connection) -> dict:
    """
    Returns every real nutrition value the product has, in the exact
    conversation/state.py known_facts shape ({attribute: {value, unit,
    source}}), so it can be merged straight into a conversation_state's
    known_facts or passed to generation/llm.py::generate_answer() as-is.

    Built for health_assessment/nutrition_assessment questions ("is it
    healthy", "should I buy it") — confirmed real gap 2026-08-20: those
    intents only ever saw known_facts the user happened to have already
    asked about explicitly earlier in the session (via record_fact() on
    the product_fact route). A first question like "is it healthy" with no
    prior nutrition question in the conversation got no product facts at
    all and fell back to generic KB retrieval, which has no per-product
    health verdict to retrieve — an honest but useless "insufficient
    evidence"/low-confidence answer even though products.sqlite has the
    actual numbers the whole time. This matches the project's own
    evidence-hierarchy principle (product facts first, KB interpretation
    second) rather than making it conditional on turn order.
    """
    row = get_product_row(product_id, conn)
    if row is None:
        return {}
    nutrition = json.loads(row["nutrition_json"] or "{}")
    values = nutrition.get("values", {})
    facts = {}
    for field, value in values.items():
        if value is None or field not in NUTRITION_LABELS:
            continue
        _, unit = NUTRITION_LABELS[field]
        facts[field] = {"value": value, "unit": unit, "source": "products.sqlite"}
    return facts


def answer_product_fact(product_id: str, fact_field: str, conn: sqlite3.Connection) -> str:
    """
    Builds a [FACT]-tagged answer straight from the products table, in
    the same claim-typing format generation/llm.py's prompt enforces, so
    downstream display code doesn't need two answer formats.
    """
    row = get_product_row(product_id, conn)
    if row is None:
        # Router resolved a product_id that isn't in the table — a data
        # sync bug (ingestion out of date), not a routing failure, so
        # surface it plainly rather than silently falling back.
        return f"[UNCERTAIN] No product record found for '{product_id}' in products.sqlite."

    name = row["name"]

    if fact_field in NUTRITION_FIELDS:
        nutrition = json.loads(row["nutrition_json"] or "{}")
        basis = nutrition.get("basis", "unknown basis")
        value = nutrition.get("values", {}).get(fact_field)
        label, unit = NUTRITION_LABELS.get(fact_field, (fact_field, ""))

        if value is None:
            return (
                f"[UNCERTAIN] {name}'s nutrition data doesn't include a value for "
                f"{label} (products.sqlite, {product_id})."
            )
        return (
            f"[FACT] {name} contains {value}{unit} of {label} ({basis.replace('_', ' ')}) "
            f"(products.sqlite, {product_id})."
        )

    if fact_field == "fssai_license":
        license_no = row["fssai_license"]
        co_license = row["co_licensee_fssai"]
        if license_no is None:
            return (
                f"[UNCERTAIN] {name}'s FSSAI license number was not clearly visible on the "
                f"submitted label and is recorded as missing, not zero or unknown-but-real "
                f"(products.sqlite, {product_id})."
            )
        if co_license:
            return (
                f"[FACT] {name} carries two FSSAI license numbers: {license_no} and "
                f"{co_license} (co-licensee) (products.sqlite, {product_id})."
            )
        return (
            f"[FACT] {name}'s FSSAI license number is {license_no} "
            f"(products.sqlite, {product_id})."
        )

    if fact_field == "ingredients_raw":
        return f"[FACT] {name}'s declared ingredients: {row['ingredients_raw']} (products.sqlite, {product_id})."

    if fact_field.startswith("ingredient:"):
        ing_name = fact_field.split(":", 1)[1]
        ingredients = json.loads(row["ingredients_parsed_json"] or "[]")
        match = next(
            (ing for ing in ingredients if (ing.get("name") or "").strip().lower() == ing_name),
            None,
        )
        if match is None:
            # Shouldn't happen — query_router only sets this field after
            # finding the same name in this product's own ingredient list.
            return f"[UNCERTAIN] Expected to find '{ing_name}' in {name}'s ingredient list but it was not present (products.sqlite, {product_id})."
        return (
            f"[FACT] Yes, {ing_name} is a declared ingredient in {name} "
            f"(products.sqlite, {product_id}). The label does not disclose an exact "
            f"quantity or percentage for individual ingredients beyond QUID-flagged ones, "
            f"so no amount can be given for it."
        )

    if fact_field == "allergens":
        contains = json.loads(row["allergens_contains_json"] or "[]")
        may_contain = json.loads(row["allergens_may_contain_json"] or "[]")
        parts = []
        if contains:
            parts.append(f"contains {', '.join(contains)}")
        if may_contain:
            parts.append(f"may contain {', '.join(may_contain)}")
        if not parts:
            parts.append("no declared allergens")
        return f"[FACT] {name} {'; '.join(parts)} (products.sqlite, {product_id})."

    if fact_field == "pack_size":
        pack = json.loads(row["pack_size_json"] or "{}")
        return (
            f"[FACT] {name}'s pack size is {pack.get('value')}{pack.get('unit')} "
            f"(products.sqlite, {product_id})."
        )

    if fact_field == "brand":
        return f"[FACT] {name} is made by {row['brand']} (products.sqlite, {product_id})."

    if fact_field == "category":
        return f"[FACT] {name} is categorized as {row['category']} (products.sqlite, {product_id})."

    return f"[UNCERTAIN] Recognized a product-fact query for {name} but no handler exists yet for field '{fact_field}'."


def answer_ingredient_or_allergen(product_id: str, name: str, conn: sqlite3.Connection) -> str:
    """
    Fuzzy-matches `name` (arbitrary text an LLM extracted from a user
    question — may be misspelled, paraphrased, or plural) against this
    product's REAL declared ingredients and allergens, and returns a
    grounded [FACT]/[UNCERTAIN] answer. Built for the tool-calling agent
    (src/agent/tools.py) as the replacement for
    routing/query_router.py's _match_ingredient_mention/_match_allergen_mention
    — those required an exact whole-word token match against the query
    text, which is exactly the class of brittleness (typos, "meaning of"
    vs "is there", a generic word like "sugar" colliding with unrelated
    nutrition questions) that caused every routing bug found 2026-08-20/21.
    Here the LLM has already decided the question IS about a specific
    named ingredient/allergen; this function's only job is to check it
    against real data and report honestly, so it can be much more lenient
    (difflib fuzzy match, not exact substring) without the false-positive
    risk that came from also having to DECIDE relevance from raw query text.
    """
    import difflib

    row = get_product_row(product_id, conn)
    if row is None:
        return f"[UNCERTAIN] No product record found for '{product_id}' in products.sqlite."

    product_name = row["name"]
    query = (name or "").strip().lower()
    if not query:
        return f"[UNCERTAIN] No ingredient or allergen name was given to check against {product_name}."

    contains = json.loads(row["allergens_contains_json"] or "[]")
    may_contain = json.loads(row["allergens_may_contain_json"] or "[]")
    allergen_values = [a.lower() for a in contains + may_contain]

    def _fuzzy_hit(candidates: list[str]) -> str | None:
        for c in candidates:
            if query in c or c in query:
                return c
        matches = difflib.get_close_matches(query, candidates, n=1, cutoff=0.6)
        return matches[0] if matches else None

    # Ingredients checked BEFORE allergens (swapped 2026-08-22, systematic
    # audit finding): allergen names are often broad categories ("milk",
    # "tree nut") while ingredients_parsed_json has the SPECIFIC declared
    # form with a recoverable quantity ("milk solids" — 23%, "cashew" —
    # 1.4%) — checking allergens first meant a query like "how much cashew
    # is in this" always short-circuited to the generic allergen-list
    # answer and never reached the quantity-recovery logic below, even
    # though a real, specific answer was available. A query that's
    # genuinely allergen-only (e.g. "does this have peanut" where peanut
    # is only a cross-contamination "may contain" note with no actual
    # ingredient entry) still correctly falls through to the allergen
    # check afterward — this reordering only changes behavior when BOTH
    # would have matched, always picking the more specific, more
    # informative answer.
    ingredients = json.loads(row["ingredients_parsed_json"] or "[]")
    ingredient_names = [(ing.get("name") or "").strip().lower() for ing in ingredients if ing.get("name")]
    ingredient_hit = _fuzzy_hit(ingredient_names)
    if ingredient_hit:
        # Recover a quantity annotation the label states right next to this
        # ingredient's name (e.g. "Caffeine (10 mg/100g)") — like the
        # vegetable-oil fallback above, ingredients_parsed_json's own
        # `component` field doesn't carry this, only ingredients_raw does.
        # Confirmed real 2026-08-21: "how much caffeine does this have?"
        # for Diet Coke got no real answer from this function (the
        # boilerplate "no amount can be given"), so the model fell back to
        # a general regulatory LIMIT chunk and wrongly presented that as
        # the product's actual caffeine content — a real value (10 mg/100g)
        # was sitting in ingredients_raw the whole time. Only treat the
        # parenthetical as a quantity if it looks like one (starts with a
        # number) — a parenthetical like "(phosphoric acid)" naming a
        # component, not an amount, must not be misread as one.
        quantity_note = ""
        qty_match = re.search(
            re.escape(ingredient_hit) + r"\s*\(([\d.]+\s*(?:mg|g|mcg|%|ppm)[^)]*)\)",
            row["ingredients_raw"] or "", re.IGNORECASE,
        )
        if qty_match:
            quantity_note = f" The label states {qty_match.group(1).strip()}."

        return (
            f"[FACT] Yes, {ingredient_hit} is a declared ingredient in {product_name} "
            f"(products.sqlite, {product_id})." + quantity_note + (
                "" if quantity_note else
                " The label does not disclose an exact quantity or percentage for individual "
                "ingredients beyond QUID-flagged ones, so no amount can be given for it."
            )
        )

    # INS-code-based match (2026-08-24): catches the case the name-based
    # fuzzy match above structurally can't — an additive declared on the
    # label only by its functional class + INS number (e.g. "Dough
    # Conditioner (INS 223)", "Raising Agent 500(ii)") never contains its
    # actual chemical name, so a query for that chemical name ("sulphite",
    # "sodium bicarbonate") can't fuzzy-match the label text no matter how
    # lenient the cutoff. Cross-checks the query against the KB's own real
    # common name for each INS code this product actually declares (see
    # _get_ins_name_index's docstring) — confirms via the product's own
    # data, not a guess, and the answer still quotes the product's own
    # label wording, not the KB's canonical name, so it stays grounded in
    # what's actually printed on the pack.
    ins_name_index = _get_ins_name_index()
    for ing in ingredients:
        ing_name_raw = (ing.get("name") or "").strip()
        for code in INS_CODE_RE.findall(ing_name_raw.lower()):
            common_names = ins_name_index.get(code, [])
            if any(query in cn or cn in query for cn in common_names):
                quantity_note = ""
                qty_match = re.search(
                    re.escape(ing_name_raw) + r"\s*\(([\d.]+\s*(?:mg|g|mcg|%|ppm)[^)]*)\)",
                    row["ingredients_raw"] or "", re.IGNORECASE,
                )
                if qty_match:
                    quantity_note = f" The label states {qty_match.group(1).strip()}."
                return (
                    f"[FACT] Yes — {product_name}'s label declares '{ing_name_raw}', which is "
                    f"{common_names[0]} (INS {code}) (products.sqlite, {product_id})." + quantity_note + (
                        "" if quantity_note else
                        " The label does not disclose an exact quantity or percentage for individual "
                        "ingredients beyond QUID-flagged ones, so no amount can be given for it."
                    )
                )

    allergen_hit = _fuzzy_hit(allergen_values)
    if allergen_hit:
        return answer_product_fact(product_id, "allergens", conn)

    # Fallback against the raw label text (2026-08-21): ingredients_parsed_json
    # is source-data, not something this project generates — confirmed real
    # for kurkure_masala_munch: the label says "Edible Vegetable Oil (Rice
    # Bran Oil)" but products_compiled.json only kept the specific
    # parenthetical ("rice bran oil") as the parsed name, silently dropping
    # the generic category term ("vegetable oil") a user is just as likely
    # to ask about. ingredients_raw is the literal, authoritative label
    # text and doesn't lose that generic term, so check it directly before
    # giving up — this function is only ever called once the model has
    # already decided the question names a specific ingredient (see
    # docstring), so a plain substring check here carries the same low
    # false-positive risk as the exact-match branch in _fuzzy_hit above.
    raw_text = (row["ingredients_raw"] or "").lower()
    if query and query in raw_text:
        return (
            f"[FACT] Yes, {product_name}'s label lists '{name}' (products.sqlite, {product_id}). "
            f"The label does not disclose an exact quantity or percentage for individual "
            f"ingredients beyond QUID-flagged ones, so no amount can be given for it."
        )

    return (
        f"[FACT] '{name}' was not found among {product_name}'s declared ingredients or allergens "
        f"(products.sqlite, {product_id})."
    )
