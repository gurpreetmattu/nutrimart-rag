"""
test_questions.py — starter eval set for the naive-vs-hybrid comparison.

Structure: each question has an `expects` field describing what a correct
retrieval should surface (prose, for manual reading — kept as-is, this
predates automated scoring). `difficulty_for_baseline` is a prediction, not
a measured result — it's what we expect the NAIVE retriever to struggle
with, based on known baseline design gaps (no doc_type filtering, no
cross-file/cross-entity linking, no reranking to break score ties). Run
these against both pipelines once both exist; don't just trust the
predictions.

Phase 7 (`eval/run_phase7_comparison.py`, `eval/phase7_metrics.py`) adds
structured fields for automated scoring, only where a question actually
supports that kind of check:
- `relevant_chunks` (q01–q09 only): list of (source_file, heading_prefix)
  ground-truth pairs for Recall@k/MRR. Prefixes, not exact headings — some
  real chunk `heading` payload values carry inline markdown commentary as
  literal text (e.g. nutrition_knowledge_base.md's Chunk 9 is stored as
  `"Chunk 9 *(new — recovered this session...)*"`), confirmed directly via
  Qdrant `scroll()`, not guessed. Match with `.startswith()`, never `==`.
- `expected_route` / `expected_product_id` / `expected_fact_field`
  (q12–q20 only): structured transcription of what `expects` already says
  in prose, for automated routing-accuracy scoring.
- q11 (trap question) gets neither `relevant_chunks` nor `reference_answer`
  — there's no single correct chunk to recall; its pass/fail signal is the
  faithfulness metric (did the answer avoid fabricating a number), not
  retrieval recall. q10 (DATEM) USED to be in this category but no longer
  is — see its own note below.

2026-08-24 addition — q01–q10 and q21–q30 (20 total) are the RAG-eval-
eligible set: every one of them has `relevant_chunks` (real, KB-verified
ground truth, not guessed) and now also `reference_answer` (a written
reference answer, grounded the same way), added specifically to support a
RAGAS-style faithfulness/context-recall pass — the missing piece flagged
when RAGAS was first discussed for this project (context recall needs an
actual reference answer to decompose into claims, not just a prose
`expects` description meant for manual reading). q12–q20 are deliberately
EXCLUDED from RAG eval — they hit the deterministic `product_fact` SQL
route and never touch retrieval/generation at all, so a RAG metric has
nothing to measure on them; they still serve their original purpose
(routing-accuracy regression, scored separately).

q21–q30 were added 2026-08-24 specifically because 10 questions was judged
too thin a set for a credible RAGAS run — every one of them is grounded in
real, directly-verified KB chunk text and, where possible, a real
product's actual declared ingredient (not invented scenarios): two are
genuine open regulatory gaps tied to real products (q22: INS 160c in
Kurkure, q23: INS 627/631 in Yippee — both confirmed to have no FSSAI
category-limit table in the source document, so the correct answer is an
honest [UNCERTAIN], not a fabricated number), one tests finding the FULLER
of two sources rather than stopping at a scope-limited one (q21: INS 223
in McVitie's — fssai_knowledge_base.md's own Chunk 41 explicitly disclaims
permitted-level info, but ingredient_knowledge_base.md's INS 223 entry has
the real 50 mg/kg figure), one is a same-product contrast pair with q23
(q24: INS 551 in the same Yippee seasoning, a genuinely resolved limit),
two test epistemic calibration on PROVISIONAL/secondary-source-only chunks
(q25: Diet Coke caffeine, q26: curd/dahi standard), two test
claims-advertising doc_type precision (q27: comparative/equivalence
claims, q28: health claims), one is real cross-chunk synthesis grounded in
Cadbury Dairy Milk's actual label wording (q29), and one tests correctly
conveying "voluntary, not mandatory" rather than assuming any fortified
product is legally compelled to be (q30).
"""

QUESTIONS = [
    # --- Easy: single-fact lookups a naive retriever should nail ---
    {
        "id": "q01",
        "query": "what is the FSSAI permitted limit for BHA in breakfast cereals",
        "expects": "fssai_knowledge_base.md, Chunk 4 (antioxidants) — 0.005% / 50ppm for RTE dry breakfast cereals",
        "difficulty_for_baseline": "easy",
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 4")],
        "reference_answer": "The FSSAI permitted limit for BHA in ready-to-eat dry breakfast cereals is 0.005% (50 ppm) — tighter than the general 0.02% limit that applies to edible oils and fats.",
    },
    {
        "id": "q02",
        "query": "what does nature-identical flavouring mean",
        "expects": "fssai_knowledge_base.md Chunk 39 or ingredient_kb_tier2.md's elevated entry — same content, two files, good test of whether baseline returns a duplicate-content chunk from either",
        "difficulty_for_baseline": "easy",
        # Ground truth is the canonical regulatory source (Chunk 39); the
        # Tier2 elevated entry is an acceptable duplicate-content bonus,
        # not a separate required item — recall_at_k treats this list as
        # "all items required," so listing both would wrongly turn a
        # single acceptable answer into a half-credit result.
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 39")],
        "reference_answer": "Nature-identical flavouring substances are chemically isolated from aromatic raw materials, or fully synthetic, but are chemically identical to substances that occur naturally in food — distinct from natural flavours (obtained by physical processes from natural raw materials only) and artificial flavouring substances (not identified in any natural food product at all).",
    },
    {
        "id": "q03",
        "query": "how much trans fat is allowed in vanaspati",
        "expects": "fssai_knowledge_base.md Chunk 31 (vanaspati) — 2% by weight",
        "difficulty_for_baseline": "easy",
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 31")],
        "reference_answer": "Vanaspati (hydrogenated vegetable oil) must not exceed 2% trans fatty acids by weight under FSSAI regulations, must be fortified with synthetic Vitamin A (minimum 25 IU/gram at packing), and caps residual nickel from the hydrogenation catalyst at 1.5 ppm.",
    },

    # --- Medium: requires distinguishing near-identical chunks ---
    {
        "id": "q04",
        "query": "can a product say low sugar",
        "expects": "fssai_knowledge_base.md Chunk 20 (claims_advertising doc_type) specifically — NOT Chunk 5 (regulatory doc_type, general sweetener permitted-use levels). Naive retriever has no doc_type filter, so it's a fair test of whether embedding similarity alone picks the right one.",
        "difficulty_for_baseline": "medium — this is the exact case doc_type filtering exists to solve",
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 20")],
        "reference_answer": "A product can only claim 'low sugar' if it contains 5g or less of sugars per 100g (or 2.5g or less per 100ml); a 'sugar free' claim requires 0.5g or less per 100g/100ml. This is a stricter marketing-claim threshold under FSSAI's Advertising and Claims Regulations, distinct from WHO's general ~10%-of-energy dietary sugar-intake guidance.",
    },
    {
        "id": "q05",
        "query": "is Diet Coke's sweetener within the legal limit",
        "expects": "fssai_knowledge_base.md Chunk 50 (beverage-specific sweetener ppm) — more precise than the general Chunk 5 table. Tests whether category-specific chunks outrank general ones on pure similarity.",
        "difficulty_for_baseline": "medium",
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 50")],
        "reference_answer": "Diet Coke's sweeteners must comply with FSSAI's category-specific limits for carbonated beverages: aspartame up to 700 ppm and acesulfame potassium up to 300 ppm. Diet Coke declares both 951 (aspartame) and 950 (acesulfame potassium), and both are within these limits.",
    },
    {
        "id": "q06",
        "query": "what's the difference between refined and raw vegetable oil",
        "expects": "fssai_knowledge_base.md Chunk 28 (general definitions) vs Chunk 32 (Ch 2.2 specific moisture/acid-value standard) — two valid but different-depth answers exist",
        "difficulty_for_baseline": "medium",
        # Real generated answers from both pipelines (eval_run.md/
        # eval_run_hybrid.md) use Chunk 28 and Chunk 32 together as
        # complementary (general definition + specific numeric standard),
        # not as alternatives — both required, unlike q02's true duplicate.
        "relevant_chunks": [
            ("fssai_knowledge_base.md", "Chunk 28"),
            ("fssai_knowledge_base.md", "Chunk 32"),
        ],
        "reference_answer": "Refined vegetable oil is oil that, after extraction, has been deacidified, degummed, bleached, and steam-deodourised using only permitted processing agents, with moisture capped at 0.10%, trans fat at 2% by weight, and acid value at 0.6. Raw/unrefined edible oil is obtained purely by mechanical means (expelling/pressing), optionally purified by washing/settling/filtering, with no processing aid used — it's exempt from the refined-oil purity standard but still fit for human consumption.",
    },

    # --- Hard: needs cross-entity or cross-file linking a flat retriever can't do ---
    {
        "id": "q07",
        "query": "should I pick the diet version instead of regular",
        "expects": "RESOLVED 2026-08-18 (was a hybrid-only unrescuable multi-hop case until then — see PHASE3_TESTING_LOG.md Finding 16): needs BOTH nutrition_knowledge_base.md Chunk 8c (WHO NSS practical-implications guidance) AND fssai_knowledge_base.md Chunk 5 (general sweetener-limits table) — a comparative query with no single chunk containing the full answer. Ground truth corrected 2026-08-18: originally listed Chunk 8a/Chunk 50, but live retrieval verification showed neither ever reaches the fused candidate pool for this exact query — Chunk 8c and Chunk 5 are the chunks that actually retrieve, and are now the ones tagged with the real, wired-up `comparison_group: \"sugar_vs_sweetener\"` metadata (previously inert — parsed and used for the first time in Finding 16). Baseline (naive) still cannot answer this — the comparison_group mechanism is hybrid-only, same precedent as the corrective retry and groundedness check.",
        "difficulty_for_baseline": "hard — the textbook case for why flat top-k retrieval alone isn't enough; hybrid resolves it via a narrow, tag-based override (Finding 16), baseline still can't",
        "relevant_chunks": [
            ("nutrition_knowledge_base.md", "Chunk 8c"),
            ("fssai_knowledge_base.md", "Chunk 5"),
        ],
        "reference_answer": "Per WHO guidance, switching from a sugar-sweetened to a non-sugar-sweetened ('diet') version doesn't automatically make a product healthier — non-sugar sweeteners have no nutritional value, and overall dietary quality is often largely unaffected by the substitution, especially since a reduction in sugar intake can be achieved without sweeteners at all (e.g. fruit, unsweetened alternatives). FSSAI's own sweetener rules only govern legal permitted levels (e.g. Diet Coke's sweeteners are within limit), which answers whether it's legal to sell, not whether it's the healthier choice.",
    },
    {
        "id": "q08",
        "query": "is the caramel colour in this product a health concern",
        "expects": "fssai_knowledge_base.md Chunk 37 (4-MEI limits + EFSA/JECFA context) — long chunk covering both regulatory limit AND health interpretation; good test of whether one well-written chunk beats needing multiple",
        "difficulty_for_baseline": "medium",
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 37")],
        "reference_answer": "Caramel colour comes in four regulatory types; only the ammonia-process types carry a 4-MEI limit — Type III (150c) capped at 300 mg/kg, Type IV (150d) at 1000 mg/kg. 4-MEI has drawn international regulatory scrutiny (e.g. California Prop 65) as a possible carcinogen based on animal studies, but FSSAI's framework treats it as a controlled-limit byproduct rather than a prohibited substance — permitted use within these ceilings is not itself a documented health concern.",
    },
    {
        "id": "q09",
        "query": "why does this ketchup need a preservative but fresh tomatoes don't",
        "expects": "no single chunk answers this directly — requires combining sodium benzoate's function (Tier 1 ingredient KB) with general preservative rationale (fssai_knowledge_base.md Chunk 34, justification for use). Interpretive synthesis, not lookup.",
        "difficulty_for_baseline": "hard",
        "relevant_chunks": [
            ("ingredient_knowledge_base.md", "INS 211 — Sodium Benzoate"),
            ("fssai_knowledge_base.md", "Chunk 34"),
        ],
        "reference_answer": "Sodium benzoate (INS 211) is added to ketchup as a preservative to inhibit bacterial, yeast, and mould growth in the acidic sauce, extending shelf life after processing/opening — a need fresh tomatoes don't have since they haven't been turned into a shelf-stable product. FSSAI permits sodium benzoate up to 750 ppm (calculated as benzoic acid) in tomato ketchup specifically.",
    },

    # --- Honest-gap tests: baseline should NOT confidently answer these ---
    {
        "id": "q10",
        "query": "what is the exact FSSAI permitted level of DATEM in bread",
        "expects": "RESOLVED 2026-08-18 (was an open-gap trap question until then — see PHASE3_TESTING_LOG.md Finding 13): ingredient_knowledge_base.md's 472e entry now states the real FSSAI answer, directly confirmed against Appendix A: GMP (Good Manufacturing Practice — no fixed numeric ceiling) for bread specifically, 10,000 ppm max for biscuits. Correct behavior is now to state this real answer with a [FACT]/[REGULATORY] citation to the 472e entry, NOT to hedge or return insufficient-evidence — that would now be under-confident given a real primary-source confirmation exists. No longer a hallucination-risk trap question; retest as a normal retrieval-accuracy case.",
        "difficulty_for_baseline": "medium — was a trap question until the KB gap was resolved 2026-08-18; now tests whether GMP (not a numeric ppm figure) gets stated correctly rather than the model inventing a number to match the question's phrasing (\"exact...level\" implies a number, but the real answer is a qualitative status)",
        "relevant_chunks": [("ingredient_knowledge_base.md", "INS 472e")],
        "reference_answer": "The FSSAI-permitted level of DATEM (INS 472e) is expressed as Good Manufacturing Practice (GMP) for bread specifically — no fixed numeric ppm ceiling — while biscuits carry a 10,000 ppm maximum. There is no single 'exact' numeric figure for bread because GMP is a qualitative permission, not a quantitative one.",
    },
    {
        "id": "q11",
        "query": "how much paprika colour is allowed in Kurkure specifically",
        "expects": "same pattern as q10 — INS 160c is a documented genuine gap. Watch for the baseline confidently citing an unrelated caramel-colour (150c) limit due to string/embedding similarity between '160c' and '150c'.",
        "difficulty_for_baseline": "trap question — specifically probes code-confusion risk (160c vs 150c)",
    },

    # --- Product-fact questions that should NEVER hit retrieval at all ---
    {
        "id": "q12",
        "query": "how many calories are in Parle-G",
        "expects": "This should be answered via direct SQL lookup against products.sqlite, not retrieval. If the pipeline sends this to the vector search at all, that's a routing bug, not a retrieval-quality issue — flag separately from Recall@k scoring.",
        "difficulty_for_baseline": "N/A — tests query routing, not retrieval",
        "expected_route": "product_fact",
        "expected_product_id": "parle_g_original",
        "expected_fact_field": "energy_kcal",
    },
    {
        "id": "q13",
        "query": "does McVitie's have two FSSAI license numbers",
        "expects": "Same as q12 — direct product-fact lookup (co_licensee_fssai field), should bypass retrieval entirely.",
        "difficulty_for_baseline": "N/A — tests query routing",
        "expected_route": "product_fact",
        "expected_product_id": "mcvities_digestive",
        "expected_fact_field": "fssai_license",
    },

    # --- Routing regression tests (routing/query_router.py), added after
    # PHASE3_TESTING_LOG.md Finding 6 was fixed. q12/q13 above cover the
    # original failure; these extend coverage to other fact fields and to
    # the router's two safety mechanisms: the regulatory-override terms
    # and ambiguous-product tie detection. Predictions verified directly
    # against classify_query() — see Finding 6's fix note. ---
    {
        "id": "q14",
        "query": "how much protein does Yogabar's protein bar have",
        "expects": "product_fact route — product_id=yogabar_daily_protein_bar_dark_chocolate_cranberry, fact_field=protein_g. Direct SQL lookup, bypasses retrieval.",
        "difficulty_for_baseline": "N/A — tests query routing",
        "expected_route": "product_fact",
        "expected_product_id": "yogabar_daily_protein_bar_dark_chocolate_cranberry",
        "expected_fact_field": "protein_g",
    },
    {
        "id": "q15",
        "query": "what are the allergens in Cadbury Dairy Milk",
        "expects": "product_fact route — product_id=cadbury_dairy_milk, fact_field=allergens. Tests a non-nutrition fact field (allergens_contains_json/allergens_may_contain_json).",
        "difficulty_for_baseline": "N/A — tests query routing",
        "expected_route": "product_fact",
        "expected_product_id": "cadbury_dairy_milk",
        "expected_fact_field": "allergens",
    },
    {
        "id": "q16",
        "query": "what is the pack size of Lay's Classic Salted chips",
        "expects": "product_fact route — product_id=lays_classic_salted, fact_field=pack_size. Tests the pack_size_json field.",
        "difficulty_for_baseline": "N/A — tests query routing",
        "expected_route": "product_fact",
        "expected_product_id": "lays_classic_salted",
        "expected_fact_field": "pack_size",
    },
    {
        "id": "q17",
        "query": "which company makes Yakult",
        "expects": "product_fact route — product_id=yakult_probiotic_drink, fact_field=brand. Tests the brand fact field, a single-product brand (no ambiguity risk, unlike Coca-Cola/Diet Coke).",
        "difficulty_for_baseline": "N/A — tests query routing",
        "expected_route": "product_fact",
        "expected_product_id": "yakult_probiotic_drink",
        "expected_fact_field": "brand",
    },
    {
        "id": "q18",
        "query": "is Coca-Cola's sugar content safe",
        "expects": "retrieval route, NOT product_fact — even though 'sugar content' matches a fact-field keyword and the query names a product. Tests REGULATORY_OVERRIDE_TERMS ('safe') correctly forcing retrieval. Also compounded by q19's ambiguity (Coca-Cola brand shared by two products), so this alone doesn't isolate the override mechanism — see q19.",
        "difficulty_for_baseline": "N/A — tests query routing",
        "expected_route": "retrieval",
    },
    {
        "id": "q19",
        "query": "how much sodium is in Coca-Cola",
        "expects": "retrieval route, NOT product_fact, despite no override term present and 'sodium' matching a fact-field keyword. Tests find_product()'s tie-breaking: 'Coca-Cola' brand is shared by both coca_cola_original and diet_coke, both score equally, so the router refuses to guess (product_id=None) rather than picking one arbitrarily. This is the negative-space test for q18 — isolates the ambiguity mechanism from the override-term mechanism.",
        "difficulty_for_baseline": "N/A — tests query routing",
        "expected_route": "retrieval",
    },
    {
        "id": "q20",
        "query": "how much fibre does Britannia Brown Bread have",
        "expects": "RESOLVED 2026-08-22 (was a documented routing gap until then): dietary_fibre_g turns out to genuinely exist in nutrition_json for 8/23 catalog products, including Britannia Brown Bread (2.8g) — the field was real, it just wasn't wired into NUTRITION_FIELD_PATTERNS/NUTRITION_LABELS yet. Now correctly routes to product_fact with fact_field=dietary_fibre_g and answers directly. A product that doesn't track this field (e.g. Parle-G) still gets a graceful [UNCERTAIN], not a crash or a wrong number.",
        "difficulty_for_baseline": "N/A — tests query routing (previously a known gap, now resolved)",
        "expected_route": "product_fact",
        "expected_product_id": "britannia_brown_bread",
        "expected_fact_field": "dietary_fibre_g",
    },

    # --- q21-q30, added 2026-08-24: RAG-eval expansion (10 -> 20 questions),
    # every one grounded in real, directly-verified KB chunk text and (where
    # applicable) a real product's actual declared ingredient — see the
    # module docstring's 2026-08-24 note for the full rationale. ---
    {
        "id": "q21",
        "query": "what is the FSSAI permitted level of the sulphite preservative used in McVitie's Digestive biscuits",
        "expects": "ingredient_knowledge_base.md's INS 223 entry (explicitly noted as 'fuller than the trunk file's Chunk 41') states the real permitted level: 50 mg/kg in cakes/cookies/biscuits/crackers (Table 7). Good test of whether retrieval finds the MORE COMPLETE source rather than stopping at fssai_knowledge_base.md's Chunk 41 alone, which looks authoritative (regulatory doc_type, names McVitie's directly) but explicitly disclaims stating permitted-use levels.",
        "difficulty_for_baseline": "hard — needs the ingredient-KB entry specifically, not the more obvious-looking but scope-limited fssai_knowledge_base.md chunk",
        "relevant_chunks": [("ingredient_knowledge_base.md", "INS 223")],
        "reference_answer": "Sodium metabisulphite (INS 223), the sulphite preservative in McVitie's Digestive, is permitted up to 50 mg/kg in cakes/cookies/biscuits/crackers (Table 7) under FSSAI rules — one of the lower permitted ceilings among common additives, reflecting sulphite's allergen sensitivity (affecting an estimated 1% of the general population, rising to 3.9-5% among asthmatics).",
    },
    {
        "id": "q22",
        "query": "what is the FSSAI permitted limit for the colour additive used in Kurkure Masala Munch",
        "expects": "Genuine open regulatory gap — ingredient_knowledge_base.md's INS 160c (Paprika Oleoresin) entry confirms FSSAI's 2011 Appendix A lists 160c only in its identification index (name + function class), with no colour-limits-by-category table anywhere in the document. Correct answer is [UNCERTAIN]/honest-gap, NOT a fabricated ppm figure — tests whether the model resists inventing a number just because the question's phrasing ('what is the limit') implies one exists.",
        "difficulty_for_baseline": "trap question — genuine document-coverage gap, not a 'not permitted' finding",
        "relevant_chunks": [("ingredient_knowledge_base.md", "INS 160c")],
        "reference_answer": "There is no FSSAI category-specific permitted limit available for INS 160c (paprika oleoresin) in this knowledge base — FSSAI's 2011 Appendix A confirms 160c is a recognized additive but this document version contains no colour-limits table for any category, so a specific ppm ceiling for Kurkure's savoury-snacks category cannot be stated. Only international ADI figures exist (JECFA 0-1.5 mg/kg bw/day, EFSA 24 mg/kg bw/day).",
    },
    {
        "id": "q23",
        "query": "is the flavour enhancer used in Yippee Magic Masala Noodles within FSSAI's permitted limit",
        "expects": "Genuine open regulatory gap — same pattern as q22/160c: FSSAI's 2011 Appendix A confirms INS 627/631/635 exist in the regulatory system (identification index only) but has no flavour-enhancer-limits table covering instant noodles/seasoning. Correct answer is [UNCERTAIN], not a fabricated ppm limit.",
        "difficulty_for_baseline": "trap question — genuine document-coverage gap, not a 'not permitted' finding",
        "relevant_chunks": [("ingredient_knowledge_base.md", "INS 627 / 631 / 635")],
        "reference_answer": "There is no FSSAI category-specific permitted limit available for the 5'-ribonucleotide flavour enhancers (INS 627/631/635) used in Yippee's masala seasoning — FSSAI's 2011 Appendix A confirms they're recognized additives but its 15 food-category tables don't include a flavour-enhancer-limits table for instant noodles. JECFA classifies this group as 'ADI not specified,' reflecting low toxicological concern, not confirmed permission at a specific level.",
    },
    {
        "id": "q24",
        "query": "what is the maximum permitted amount of the anticaking agent in Yippee Noodles' masala seasoning",
        "expects": "fssai_knowledge_base.md Chunk 40 — synthetic amorphous silicon dioxide (INS 551) may be used as an anticaking agent in powder flavouring substances up to 2% by weight maximum. Real, verified, resolved answer — deliberately paired with q23 (same product's masala seasoning, but a genuinely open gap for a different additive) to test whether the system correctly distinguishes a confidently-answerable ingredient from an honest-gap one within the SAME product.",
        "difficulty_for_baseline": "easy — but a meaningful contrast case against q23, not a standalone easy question",
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 40")],
        "reference_answer": "Synthetic amorphous silicon dioxide (INS 551), the anticaking agent in Yippee's masala seasoning, may be used up to a maximum of 2% by weight in powder flavouring substances under FSSAI regulations.",
    },
    {
        "id": "q25",
        "query": "does Diet Coke's caffeine content comply with FSSAI's caffeine regulation",
        "expects": "fssai_knowledge_base.md Chunk 43 — ordinary carbonated soft drinks are capped at 200 ppm caffeine; Diet Coke (100 mg/L per its own declared caffeine content) sits comfortably under this. IMPORTANT: this chunk is explicitly marked PROVISIONAL/secondary-source, not verified against primary gazette text — a fully faithful answer should ideally surface that caveat rather than stating the figure with the same confidence as a primary-source-verified one (contrast with q05's Chunk 50, which IS primary-source-confirmed for the same product). Tests epistemic calibration, not just factual correctness.",
        "difficulty_for_baseline": "medium — factually easy, but tests whether provenance/confidence is conveyed honestly",
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 43")],
        "reference_answer": "Diet Coke's caffeine content (100 mg/L, per its own product data) is well under FSSAI's cited 200 ppm cap for ordinary carbonated soft drinks and its 300 mg/L cap for the separate 'Caffeinated Beverage' sub-category — though this specific regulation is sourced from secondary references only, not verified against FSSAI's primary gazette text.",
    },
    {
        "id": "q26",
        "query": "what is the FSSAI compositional standard for curd (dahi)",
        "expects": "fssai_knowledge_base.md Chunk 44 — full-cream curd must have >=3.0% fat, toned-milk curd >=0.5% fat, both >=8.5% SNF, titratable acidity 0.5-1.0%. Same epistemic-calibration test as q25 — this chunk is also explicitly PROVISIONAL/secondary-source only, not verified against primary gazette text.",
        "difficulty_for_baseline": "medium — factually easy, but tests whether provenance/confidence is conveyed honestly",
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 44")],
        "reference_answer": "Under FSSAI's curd/dahi standard, full-cream curd requires a minimum 3.0% milk fat, toned-milk curd a minimum 0.5% fat, both require a minimum 8.5% solids-not-fat (SNF), and titratable acidity of 0.5-1.0% as lactic acid — though this figure comes from secondary sources only and hasn't been verified against FSSAI's primary gazette text.",
    },
    {
        "id": "q27",
        "query": "can Britannia Brown Bread claim it has as much fibre as an apple",
        "expects": "fssai_knowledge_base.md Chunk 23 — equivalence claims ('as much fibre as an apple') are only permitted if the reference food (apple) would itself qualify as a 'source' of that nutrient under the fibre threshold (>=3g/100g or >=1.5g/100kcal, from Chunk 22). Interpretive/conditional claims question, not a direct nutrition-fact lookup — tests whether retrieval finds the comparative-claims chunk specifically, not the more generic Chunk 22 fibre-threshold chunk alone.",
        "difficulty_for_baseline": "medium — needs the comparative-claims chunk specifically, not the more obvious nutrient-threshold chunk",
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 23")],
        "reference_answer": "An equivalence claim like 'as much fibre as an apple' is only legally permitted if the reference food (apple) itself would qualify as a 'source' of fibre under FSSAI's nutrient threshold (>=3g/100g or >=1.5g/100kcal) — the claim can't be made just because the numeric comparison happens to be true.",
    },
    {
        "id": "q28",
        "query": "can a product claim it helps reduce cholesterol",
        "expects": "fssai_knowledge_base.md Chunk 25 (health_claims doc_type) — 'Diets low in saturated fat contribute to the maintenance of normal blood cholesterol levels' is the Schedule III pre-approved claim statement, conditional on the product actually qualifying as 'low saturated fat.' Naive retriever risk: confusing this with Chunk 18/19 (fat-type claims) or Chunk 22 (nutrient thresholds) since all touch fat/cholesterol vocabulary — same doc_type-filtering test intent as q04.",
        "difficulty_for_baseline": "medium — the exact case doc_type filtering exists to solve, same pattern as q04",
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 25")],
        "reference_answer": "A product can only use the pre-approved statement 'Diets low in saturated fat contribute to the maintenance of normal blood cholesterol levels' if it actually qualifies as 'low saturated fat' under FSSAI's claims regulations — a generic 'helps reduce cholesterol' claim outside this approved wording and condition is not permitted without prior FSSAI approval.",
    },
    {
        "id": "q29",
        "query": "why does Cadbury Dairy Milk's label mention cocoa butter equivalent, and is this compliant",
        "expects": "Requires BOTH fssai_knowledge_base.md Chunk 48 (chocolate compositional minimums by type — milk chocolate needs >=25% total fat, >=2% milk fat, >=2.5% cocoa solids, >=10.5% milk solids) AND Chunk 49 (mandatory 'CONTAINS COCOA BUTTER EQUIVALENT' label declaration when vegetable fats other than cocoa butter are used) — genuine multi-chunk synthesis, no single chunk fully explains both the composition standard AND the labelling requirement. Directly grounded: Cadbury Dairy Milk's real label reads 'Contains Cocoa Butter Equivalent in addition to Cocoa Butter,' and its real ingredients list Emulsifiers (442, 476) consistent with vegetable-fat-derived equivalents.",
        "difficulty_for_baseline": "hard — needs two chunks combined, no single chunk has the full answer, same class as q06/q07/q09",
        "relevant_chunks": [
            ("fssai_knowledge_base.md", "Chunk 48"),
            ("fssai_knowledge_base.md", "Chunk 49"),
        ],
        "reference_answer": "Cadbury Dairy Milk is a milk chocolate, which under FSSAI's compositional standard must have at least 25% total fat, 2% milk fat, 2.5% cocoa solids, and 10.5% milk solids, with vegetable fat other than cocoa butter capped at 5% of the finished product. Because it contains vegetable fat used as a cocoa butter equivalent, FSSAI mandates the bold label declaration 'CONTAINS COCOA BUTTER EQUIVALENT / VEGETABLE FAT IN ADDITION TO COCOA BUTTER' — which matches the product's real label wording, so the declaration is compliant, not a red flag.",
    },
    {
        "id": "q30",
        "query": "is it mandatory for Kellogg's Corn Flakes to be fortified with vitamins and minerals",
        "expects": "fssai_knowledge_base.md Chunk 45's fortification-framework section — fortification is voluntary under the 2018 Fortification Regulations, not mandatory, unless a specific category standard separately requires it; the '+F' logo is required only wherever fortification IS claimed. Real product-grounded nuance test: Kellogg's Corn Flakes is voluntarily fortified, not legally compelled to be — tests whether the model correctly conveys 'voluntary' rather than assuming any fortified product is mandated to be so.",
        "difficulty_for_baseline": "medium — tests a specific 'voluntary not mandatory' nuance easy to get wrong by default",
        "relevant_chunks": [("fssai_knowledge_base.md", "Chunk 45")],
        "reference_answer": "No — fortification is voluntary under FSSAI's Food Safety and Standards (Fortification of Foods) Regulations, 2018, not mandatory, unless a specific category standard separately requires it. Kellogg's Corn Flakes (like Chocos, Britannia Brown Bread, and Bournvita) is voluntarily fortified and must carry the '+F' logo because it makes that claim, but it isn't legally compelled to fortify.",
    },
]


if __name__ == "__main__":
    from collections import Counter
    difficulty_counts = Counter(q["difficulty_for_baseline"].split(" ")[0] for q in QUESTIONS)
    print(f"Total questions: {len(QUESTIONS)}")
    print(f"By difficulty: {dict(difficulty_counts)}")
