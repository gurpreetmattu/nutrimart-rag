# Ingredient Knowledge Base — Tier 1 (INS-Numbered Additives)
**Discovery note:** this file was found mid-reconstruction, in a session that had already done the actual work — writing full, cited, product-scoped entries directly against `products_compiled.json` and the filtered Appendix A data (`regulatory_kb_product_scoped.json`). This supersedes the earlier assumption that "Tier 1 was never drafted" — it was. It just never made it into the Project either.

**Scope:** All INS-numbered additives across the 23 canonical products, cross-referenced against the product-scoped regulatory KB. 38 of ~40-45 entries recovered verbatim in this reconstruction pass (a handful of very minor/duplicate ones — e.g. 621/MSG, already covered in `fssai_knowledge_base.md` Chunk 7 — weren't re-pulled since they'd be redundant). **This file is INS-additives only — base/whole-food ingredients (sugar, salt, flours, spices, oils, dairy) live entirely in `ingredient_kb_tier2.md`; see the reconciliation note near the end of this file.**

**Regulatory-status labelling convention used throughout:** each entry states whether FSSAI permission was (a) confirmed with a specific numeric limit, (b) confirmed via the GMP-blanket list (no fixed ceiling, self-limiting by technical need), or (c) a **genuine gap** — no category-specific limit and not on the GMP list either, meaning the additive's legal status for that specific product category is unconfirmed, not necessarily prohibited. Do not upgrade a "genuine gap" entry to a confident regulatory claim without further primary-source work.

**Metadata convention:** `{doc_type: "ingredient", entity: "<name> (INS <code>)", ins_no: "<code>", source: "...", last_verified: "2025-08-01"}`

---

## Preservatives

### INS 211 — Sodium Benzoate
See `fssai_knowledge_base.md` Chunk 42 for the full identity/purity/gap writeup — same content, not duplicated here.

### INS 223 — Sodium Metabisulphite
**Note:** Fuller version than the trunk file's Chunk 41 — has real epidemiological sourcing.
**Used in:** McVitie's Digestive Biscuits.
**Regulatory status (FSSAI):** Permitted up to 50 mg/kg in cakes/cookies/biscuits/crackers (Table 7) — notably one of the *lower* permitted ceilings among the additives in this KB, reflecting the ingredient's allergen sensitivity.
**Health considerations:** This is the ingredient behind McVitie's "may contain sulphite" allergen declaration, and it's one of the more medically consequential additives on this list for a specific population. Sulphite sensitivity affects an estimated 1% of the general population, rising to an estimated **3.9–5% among asthmatics** specifically (based on oral/inhalation challenge studies), where reactions can range from skin rashes to bronchospasm and, rarely, severe anaphylactic-type reactions. Distinct from a true IgE-mediated food allergy — typically a direct irritant/pharmacological sensitivity to residual sulfur dioxide. EFSA's follow-up re-evaluation of the sulfite group (E220–228) found the safety margin at estimated dietary exposure levels was below the threshold considered protective for some population groups, part of why FSSAI's permitted level here (50 mg/kg) is comparatively tight.
**Source:** EFSA Panel on Food Additives, "Follow-up of the re-evaluation of sulfur dioxide (E220)... sodium metabisulfite (E223)...," 2022; Bush et al., "Prevalence of sensitivity to sulfiting agents in asthmatic patients," 1986 (PMID 3535492).
**Metadata:** `{doc_type: "ingredient", entity: "Sodium Metabisulphite (INS 223)", ins_no: "223", source: "EFSA 2022 + Bush et al. 1986", last_verified: "2025-08-01"}`

### INS 260 — Acetic Acid
**Used in:** Britannia Brown Bread; Kissan Fresh Tomato Ketchup; Maggi Hot & Sweet Chilli Tomato Sauce.
**Regulatory status:** No category-specific numeric limit found in Tables 7/12. On the **GMP-blanket list**.
**Health considerations:** No safety concerns — the same acid present in ordinary vinegar, one of the most common, well-tolerated acidulants in food.
**Source:** FSSAI Appendix A (GMP Table Provisions For All Food Categories).
**Metadata:** `{doc_type: "ingredient", entity: "Acetic Acid (INS 260)", ins_no: "260", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 282 — Calcium Propionate
**Used in:** Britannia Brown Bread.
**Regulatory status:** No category-specific numeric limit found in Table 7 (Bakery). On the **GMP-blanket list**.
**Health considerations:** Long-established, low-concern bread preservative. Propionates occur naturally in some fermented foods; strong safety record at food-additive levels, though a small, older, contested body of research explored a possible association with behavioural effects in some children — evidence here is notably weaker and less consistent than the benzoate/hyperactivity literature.
**Source:** FSSAI Appendix A.
**Metadata:** `{doc_type: "ingredient", entity: "Calcium Propionate (INS 282)", ins_no: "282", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 200 — Sorbic Acid
**Used in:** Britannia Brown Bread.
**Regulatory status:** Permitted up to 1,000 mg/kg in Bakery products (Table 7).
**Health considerations:** One of the more well-tolerated preservatives in common use; occurs naturally in some berries, long safety track record. Rare allergic-type skin reactions reported in topical/cosmetic contexts, but dietary sorbic acid is not a common food-intolerance trigger the way sulfites or benzoates can be.
**Source:** FSSAI Appendix A; general food-additive safety literature.
**Metadata:** `{doc_type: "ingredient", entity: "Sorbic Acid (INS 200)", ins_no: "200", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

---

## Acidity Regulators

### INS 296 — Malic Acid, DL-
**Used in:** Kurkure Masala Munch; McVitie's Digestive Biscuits.
**Regulatory status:** No category-specific numeric limit found in Tables 7/15. On the **GMP-blanket list**.
**Health considerations:** Naturally occurring in apples and many fruits; no safety concerns at food-additive levels.
**Source:** FSSAI Appendix A.
**Metadata:** `{doc_type: "ingredient", entity: "Malic Acid (INS 296)", ins_no: "296", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 330 — Citric Acid
**Used in:** Haldiram's Nagpur Aloo Bhujia; Kurkure Masala Munch; MAGGI Double Masala Noodles; Parle-G Biscuits; Real Fruit Power Juice; Yippee Magic Masala Noodles.
**Regulatory status:** Permitted at GMP levels across multiple relevant categories (Cereals, Bakery, Beverages, Ready-to-eat savouries).
**Health considerations:** Naturally occurring in citrus fruits, produced industrially via fermentation; one of the lowest-concern acidulants in the entire food additive system.
**Source:** FSSAI Appendix A.
**Metadata:** `{doc_type: "ingredient", entity: "Citric Acid (INS 330)", ins_no: "330", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 331(iii) — Trisodium Citrate
**Used in:** Diet Coke.
**Regulatory status:** Permitted at GMP levels in the relevant beverage sub-category.
**Health considerations:** Very low concern — a common buffering salt, no notable safety issues at food-additive levels.
**Source:** FSSAI Appendix A.
**Metadata:** `{doc_type: "ingredient", entity: "Trisodium Citrate (INS 331(iii))", ins_no: "331(iii)", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 334 — Tartaric Acid, L-
**Note:** ⚠ Still unresolved for Kurkure's specific category (savoury snacks); confirmed GMP-permitted elsewhere.
**Used in:** Kurkure Masala Munch.
**Regulatory status:** **No match found** in Table 15 (Ready-to-eat savouries) and not on the GMP-blanket list. Likely a coverage gap given how common this acidulant is, but not confirmed for *this specific category*.
**Corroborating evidence found this session:** *Pernod Ricard India Pvt. Ltd. vs. Union of India*, AIR 2015 (NOC) 1280 (Bombay HC) — a real, citable case where FSSAI itself refused a No Objection Certificate for an imported wine product on the stated ground that it contained "Tartaric Acid (INS334) and Ascorbic Acid (INS315) which are not permitted as per Appendix A of the [Food Additives] Regulations." This is a different product category (wine, not ready-to-eat savouries), so it doesn't directly settle Kurkure's case — but it's documented proof that FSSAI's own regulatory practice has treated INS 334 as absent from Appendix A for at least one category, which meaningfully corroborates (not proves) the "genuine gap" finding here. **Legal nuance worth noting:** the Bombay HC ruled that "Regulation... and Appendix" should be read disjunctively — an additive is permitted if listed in *either* the main Regulation text or Appendix A, not only if listed in both. So even confirmed absence from Appendix A alone wouldn't be dispositive; the Chapter 3 regulation text would also need checking, which this reconstruction hasn't done for 334 specifically.
**Health considerations:** Naturally occurring, well-established food acid with a long safety history (also used in winemaking, baking powder). No meaningful safety concerns at food-additive levels. EFSA's 2020 re-evaluation set a group ADI of 240 mg/kg bw/day for tartaric acid and its tartrate salts (E334–337, E354) and found no safety concern at reported exposure levels.
**Update from 2026-08-18 primary-source read:** directly read FSSAI's original 2011 Appendix A (Table 1, "List of food additives for use in bread and biscuits") — L-Tartaric acid appears there as **Bread: not listed ("-"), Biscuits: GMP**. Confirms tartaric acid genuinely IS permitted (at GMP) in at least one real FSSAI food category, not just internationally — but this document (the 2011 original Appendix A) does not contain a dedicated "ready-to-eat savouries" table at all (its category list runs Table 1–15, covering bread/biscuits, oils/fats, general food products, sugars/salt, confectionery/cocoa, milk products, and cheese — no extruded-snacks category). Kurkure's specific category likely only exists in a newer, Codex-realigned version of Appendix A (see the DATEM entry above for the same document-version discovery) that wasn't accessible this session. **Net effect: strengthens the "coverage gap, not deliberate non-permission" reading**, since 334 is now confirmed as a genuinely GMP-permitted additive elsewhere in the same regulation, but Kurkure's exact category is still unconfirmed either way.
**Source:** General food-additive safety literature; EFSA re-evaluation 2020; *Pernod Ricard India Pvt. Ltd. vs. Union of India*, AIR 2015 (NOC) 1280 (Bom), via LiveLaw.in summary; FSSAI Appendix A 2011, Table 1 (bread/biscuits — GMP for biscuits, confirmed 2026-08-18, but not Kurkure's category). **FSSAI category-specific permission for ready-to-eat savouries still not directly confirmed — likely requires the current amended Appendix A, not the 2011 original.**
**Metadata:** `{doc_type: "ingredient", entity: "Tartaric Acid (INS 334)", ins_no: "334", source: "confirmed GMP-permitted in bread/biscuits category (2011 Appendix A); savoury-snacks category still unconfirmed, likely needs a newer Appendix A version", last_verified: "2026-08-18"}`

### INS 338 — Phosphoric Acid
**Used in:** Coca-Cola; Diet Coke.
**Regulatory status:** Permitted up to 1,000 mg/kg in the relevant beverage category.
**Health considerations:** Generally recognised as safe at permitted beverage levels. Ongoing research interest in a possible association between high habitual cola intake and lower bone mineral density — more consistently linked to colas displacing calcium-rich beverages in the diet (a substitution effect) than to phosphoric acid directly depleting bone at typical intakes. Genuinely debated, not settled consensus.
**Source:** FSSAI Appendix A; general nutrition literature on cola consumption and bone health (mixed/contested findings).
**Metadata:** `{doc_type: "ingredient", entity: "Phosphoric Acid (INS 338)", ins_no: "338", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 339(i) — Sodium Hydrogen Phosphate (PHOSPHATES group member)
**Used in:** Yippee Magic Masala Noodles.
**Regulatory status:** Permitted up to 2,500 mg/kg in Flours and starches (Table 6), part of the broader PHOSPHATES group ceiling.
**Health considerations:** Phosphates as a class are generally safe at typical levels, but **cumulative intake across multiple products matters more than any single ingredient's individual limit** — a diet with several phosphate-containing processed foods can approach levels of research interest for kidney health in specific populations; a population-level dietary-pattern concern, not a single-product safety issue.
**Source:** FSSAI Appendix A.
**Metadata:** `{doc_type: "ingredient", entity: "Sodium Hydrogen Phosphate (INS 339(i))", ins_no: "339(i)", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 170(i) — Calcium Carbonate
**Used in:** Yippee Magic Masala Noodles (instant noodle powder sub-blend).
**Regulatory status:** Permitted up to 5,000 mg/kg in Flours and starches (Table 6).
**Health considerations:** Essentially inert, extremely well-established — same compound as chalk/limestone, a common calcium supplement ingredient. No safety concerns at food-additive levels.
**Source:** FSSAI Appendix A.
**Metadata:** `{doc_type: "ingredient", entity: "Calcium Carbonate (INS 170(i))", ins_no: "170(i)", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

---

## Raising Agents / Alkalis

### INS 500(i) — Sodium Carbonate
**Used in:** MAGGI Double Masala Noodles; Yippee Magic Masala Noodles.
**Regulatory status:** Permitted up to 10,000 mg/kg in the relevant noodle/pasta category.
**Health considerations:** Well-established, low-concern alkali; no significant safety issues at food-additive levels.
**Metadata:** `{doc_type: "ingredient", entity: "Sodium Carbonate (INS 500(i))", ins_no: "500(i)", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 500(ii) — Sodium Hydrogen Carbonate (Baking Soda)
**Used in:** Britannia Good Day Cashew Cookies; Cadbury Bournvita; McVitie's Digestive; Parle-G Original; Sunfeast Dark Fantasy.
**Regulatory status:** No category-specific numeric limit found in Table 7 (Bakery). On the **GMP-blanket list**.
**Health considerations:** Ordinary baking soda — one of the most familiar, well-understood, low-concern substances in the entire food system.
**Metadata:** `{doc_type: "ingredient", entity: "Sodium Bicarbonate / Baking Soda (INS 500(ii))", ins_no: "500(ii)", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 501(i) — Potassium Carbonate
**Used in:** MAGGI Double Masala Noodles; Yippee Magic Masala Noodles.
**Regulatory status:** Permitted up to 11,000 mg/kg in the relevant noodle/pasta category.
**Health considerations:** Low concern for the general population; individuals on medically-directed potassium restriction (some kidney conditions) are the relevant group for cumulative-intake awareness, not a general-population safety concern.
**Metadata:** `{doc_type: "ingredient", entity: "Potassium Carbonate (INS 501(i))", ins_no: "501(i)", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 503(ii) — Ammonium Hydrogen Carbonate
**Used in:** Britannia Good Day Cashew Cookies; McVitie's Digestive; Parle-G Original; Sunfeast Dark Fantasy.
**Regulatory status:** No category-specific numeric limit found in Table 7 (Bakery). On the **GMP-blanket list**.
**Health considerations:** Traditional raising agent (sometimes called "hartshorn") with a long history, particularly in thin, crisp baked goods. Ammonia gas fully escapes during baking in thin products, leaving no meaningful residue.
**Metadata:** `{doc_type: "ingredient", entity: "Ammonium Hydrogen Carbonate (INS 503(ii))", ins_no: "503(ii)", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 508 — Potassium Chloride
**Used in:** MAGGI Double Masala Noodles; Yippee Magic Masala Noodles.
**Regulatory status:** No category-specific numeric limit found in Table 6. On the **GMP-blanket list**.
**Health considerations:** Low concern for general population; best known as a salt substitute. Individuals with kidney conditions requiring potassium restriction are the relevant group, not a general-population concern.
**Metadata:** `{doc_type: "ingredient", entity: "Potassium Chloride (INS 508)", ins_no: "508", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 510 — Ammonium Chloride
**Used in:** Britannia Brown Bread.
**Regulatory status:** No category-specific numeric limit found in Table 7. On the **GMP-blanket list**.
**Health considerations:** Well-established bread-making aid (yeast-feeding nitrogen source); consumed almost entirely by yeast during fermentation, leaving minimal residue.
**Metadata:** `{doc_type: "ingredient", entity: "Ammonium Chloride (INS 510)", ins_no: "510", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 450(i) / 451(i) / 452(i) — Diphosphates / Triphosphates (PHOSPHATES group)
**Used in:** McVitie's Digestive; Sunfeast Dark Fantasy; Yippee Noodles (450(i)); MAGGI Noodles (451(i)); Yippee Noodles (452(i)).
**Regulatory status:** Permitted up to 2,500 mg/kg in Flours and starches (Table 6), part of the combined PHOSPHATES group ceiling.
**Health considerations:** Same cumulative-phosphate consideration as INS 339(i) — individually low-concern, but part of a class where total dietary phosphate load across multiple sources is the more relevant question.
**Metadata:** `{doc_type: "ingredient", entity: "Diphosphates/Triphosphates (INS 450(i)/451(i)/452(i))", ins_no: "450(i), 451(i), 452(i)", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

---

## Emulsifiers / Stabilizers / Thickeners

### INS 412 — Guar Gum
**Used in:** MAGGI Double Masala Noodles; Yippee Magic Masala Noodles.
**Regulatory status:** No category-specific numeric limit found in Table 6. On the **GMP-blanket list**.
**Health considerations:** Well-established soluble fibre from guar beans; no safety concerns at food-additive levels — used therapeutically as a fibre source at higher, supplement-level doses.
**Metadata:** `{doc_type: "ingredient", entity: "Guar Gum (INS 412)", ins_no: "412", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 415 — Xanthan Gum
**Used in:** Kissan Fresh Tomato Ketchup; Maggi Hot & Sweet Chilli Tomato Sauce.
**Regulatory status:** No category-specific numeric limit found in Table 12. On the **GMP-blanket list**.
**Health considerations:** One of the most widely used and well-tolerated stabilizers in the food supply.
**Metadata:** `{doc_type: "ingredient", entity: "Xanthan Gum (INS 415)", ins_no: "415", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 440 — Pectin
**Used in:** Real Fruit Power Mixed Fruit Juice.
**Regulatory status:** Permitted at GMP levels in fruit juices.
**Health considerations:** Naturally occurring soluble fibre found in fruit; no safety concerns, itself a fibre source.
**Metadata:** `{doc_type: "ingredient", entity: "Pectin (INS 440)", ins_no: "440", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 442 — Ammonium Phosphatides
**Used in:** Cadbury Dairy Milk Chocolate Bar.
**Regulatory status:** Permitted at GMP levels in the relevant cocoa/confectionery category.
**Health considerations:** Well-established chocolate-industry emulsifier, alternative to lecithin, long safety record.
**Metadata:** `{doc_type: "ingredient", entity: "Ammonium Phosphatides (INS 442)", ins_no: "442", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 476 — Polyglycerol Polyricinoleate (PGPR)
**Used in:** Amul Dark Chocolate; Cadbury Dairy Milk.
**Regulatory status:** Permitted up to 5,000 mg/kg in the relevant cocoa/confectionery category.
**Health considerations:** Derived from castor oil; well-established in chocolate manufacturing, extensive safety record.
**Metadata:** `{doc_type: "ingredient", entity: "PGPR (INS 476)", ins_no: "476", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 322 / 322(i) — Lecithin
**Note:** ⚠ Partially resolved — chocolate confirmed, bakery/biscuits still ambiguous.
**Used in:** Amul Dark Chocolate; Britannia Good Day Cashew Cookies; Cadbury Bournvita; McVitie's Digestive Biscuits; Sunfeast Dark Fantasy Choco Fills; Yogabar Protein Bar.
**Regulatory status — updated 2026-08-18 from a direct primary-source read:** FSSAI's 2011 Appendix A, Table 13 ("Cocoa powder, Chocolate, Sugar boiled confectionery, Chewing gum/Bubble gum"), Section E (Emulsifiers), lists Lecithin at **10 g/kg max for cocoa powder, GMP for chocolate** — directly relevant to Amul Dark Chocolate and Cadbury Bournvita. Table 1 (Bread and Biscuits) lists Lecithin at **Bread: GMP**, but the Biscuits column shows a dash — the table's own header note for that section says biscuit emulsifiers not individually listed instead fall under "regulation 3.1.6," so this is likely "governed by the general list, not a specific numeric entry" rather than "not permitted." **Net: chocolate use (Amul, Bournvita) is now confirmed; bakery/biscuit use (Britannia Good Day, McVitie's) is still ambiguous, not a clean gap or a clean confirmation.** Yogabar Protein Bar's category (protein bars) isn't covered by either table found.
**Health considerations:** One of the most well-established emulsifiers in food use, generally recognised as safe. The consumer-relevant consideration is **allergen sourcing** — most commonly soy-derived (as labelled here), relevant for soy-allergic consumers even though highly refined lecithin typically contains negligible residual soy protein. India requires soy declared as an allergen regardless of refinement level.
**Source:** General food-emulsifier safety literature (JECFA/EFSA consensus); FSSAI Appendix A 2011, Tables 1 and 13 (chocolate/cocoa confirmed 2026-08-18; bakery ambiguous per the table's own regulation-3.1.6 cross-reference; protein-bar category not covered by this document version).
**Metadata:** `{doc_type: "ingredient", entity: "Lecithin (INS 322)", ins_no: "322", source: "FSSAI Appendix A: chocolate/cocoa confirmed 2026-08-18, bakery ambiguous", last_verified: "2026-08-18"}`

### INS 471 — Mono- and Di-glycerides of Fatty Acids
**Note:** ⚠ Partially resolved — chocolate/cocoa confirmed, bakery still unconfirmed.
**Used in:** Britannia Good Day Cashew Cookies; Cadbury Bournvita; Sunfeast Dark Fantasy.
**Regulatory status — updated 2026-08-18:** FSSAI's 2011 Appendix A, Table 13 ("Cocoa powder, Chocolate, Sugar boiled confectionery, Chewing gum/Bubble gum"), Section E, lists "Mono and di-glycerides of edible fatty acids" at **GMP for cocoa powder, GMP for chocolate** — directly relevant to Cadbury Bournvita (cocoa-based). A separate, unrelated mention was also found in Table 12 ("food products," general cross-category list) under "Antifoaming agents" at 10 ppm max — a different use context, not the emulsifier role relevant here, kept for completeness but not treated as the operative limit. Table 1 (Bread and Biscuits) does not list this additive by name — still unconfirmed for Britannia Good Day and Sunfeast Dark Fantasy's bakery/biscuit base, same pattern as Lecithin above.
**Health considerations:** One of the most extensively used and well-studied emulsifiers in food manufacturing; broadly recognised as safe.
**Source:** General food-emulsifier safety literature; FSSAI Appendix A 2011, Tables 12 and 13 (cocoa/chocolate confirmed 2026-08-18; bakery/biscuit category still unconfirmed).
**Metadata:** `{doc_type: "ingredient", entity: "Mono- and Di-glycerides of Fatty Acids (INS 471)", ins_no: "471", source: "FSSAI Appendix A: cocoa/chocolate confirmed 2026-08-18, bakery unconfirmed", last_verified: "2026-08-18"}`

### INS 472e — DATEM (Diacetyl Tartaric Acid Esters of Glycerol)
**Used in:** Britannia Brown Bread; Britannia Good Day Cashew Cookies; McVitie's Digestive; Parle-G Original.
**Regulatory status:** **✅ RESOLVED 2026-08-18.** FSSAI Appendix A, Table 1 ("List of food additives for use in bread and biscuits"), Section B ("Emulsifying and stabilizing agents"), entry 4 — "Di-Acetyl tartaric acid esters of mono and di-glycerides" — is listed with **Bread: GMP** (Good Manufacturing Practice — permitted at the level needed for the technical purpose, no fixed numeric ceiling) and **Biscuits: 10,000 ppm max**. This directly covers all four products above: Britannia Brown Bread and Parle-G Original fall under "Bread" (GMP), Britannia Good Day and McVitie's Digestive fall under "Biscuits" (10,000 ppm max). Read directly from the extracted primary-source PDF text, not a secondary summary — table structure and column headers confirmed unambiguous (`Sl. No. | Name of additive | Bread | Biscuits`, no column-order ambiguity).
**Why earlier extraction attempts missed this:** the original Phase 3 session searched for DATEM under "Table 6 (Cereals)" and "Table 7 (Bakery)" and found it absent — those table numbers don't match this document's actual "Table 1 (Bread and Biscuits)" heading. The KB's internal Table 6/7 numbering appears to reference a different (likely newer, Codex-realigned) version of Appendix A than the one actually retrieved and read here — **this document is FSSAI's original 2011 Appendix A** (from `Food Products Standards and Food Additives Regulations, 2011, Part II`), not a current amended edition. DATEM's bread/biscuit permission is a long-standing, well-established one internationally (matches the EU's quantum-satis pattern for the same additive, found in the prior 2026-08-18 follow-up below) and unlikely to have been removed in later amendments, but a court-level confirmation would ideally re-check against the current in-force Appendix A text, not just the 2011 original.
**Health considerations:** Well-established bakery emulsifier with a long international safety record; no significant safety concerns at typical use levels.
**Prior investigation history (kept for the record, now resolved):** the original 2026-08-13 extraction searched under the wrong table numbers and found DATEM "confirmed absent." A same-day secondary source claimed FSSAI permission under "Schedule I" with unspecified "category-specific upper limits" but cited no table or number. A 2026-08-18 follow-up hit a real tool barrier trying to fetch `fssai.gov.in`'s PDFs directly (every attempt returned only the page header) but did surface the EU's quantum-satis pattern for E472e in bread as useful context. A second 2026-08-18 attempt, using a document-viewer-hosted mirror of the regulation (rather than the government PDF directly) plus a local `pypdf` text extraction, finally got real, readable primary-source text — resolving this entry.
**Source:** FSSAI, Food Safety and Standards (Food Products Standards and Food Additives) Regulations, 2011, Part II, Appendix A, Table 1 (via a Goa state government-hosted mirror of the regulation, extracted and read directly, 2026-08-18).
**Metadata:** `{doc_type: "ingredient", entity: "DATEM (INS 472e)", ins_no: "472e", source: "FSSAI Appendix A Table 1, directly confirmed 2026-08-18: Bread=GMP, Biscuits=10000ppm max", last_verified: "2026-08-18"}`

---

## Anticaking / Flour Treatment

### INS 1101(ii) — Papain (Flour Treatment Agent / Protease Enzyme)
**Used in:** Parle-G Original Gluco Biscuits.
**Regulatory status:** Not listed with a category-specific ceiling in Table 7 (Bakery). On the **GMP-blanket list** — no fixed mg/kg ceiling, self-limiting by the amount needed for the technical effect.
**Health considerations:** Well-characterised enzyme, long history of food use (also a meat tenderizer). No significant safety concerns at trace processing-aid levels; largely inactivated during baking.
**Metadata:** `{doc_type: "ingredient", entity: "Papain (INS 1101(ii))", ins_no: "1101(ii)", source: "FSSAI Appendix A (GMP Table)", last_verified: "2025-08-01"}`

### INS 1422 — Acetylated Distarch Adipate (Modified Starch)
**Used in:** Kissan Fresh Tomato Ketchup.
**Regulatory status:** No category-specific numeric limit found in Table 12 (Salts, spices, sauces). On the **GMP-blanket list**.
**Health considerations:** Modified food starches broadly recognised as safe — chemically similar to native starch with minor structural modifications, no specific health concern at typical dietary levels.
**Metadata:** `{doc_type: "ingredient", entity: "Acetylated Distarch Adipate (INS 1422)", ins_no: "1422", source: "FSSAI Appendix A (GMP Table)", last_verified: "2025-08-01"}`

### INS 551 — Silicon Dioxide
See `fssai_knowledge_base.md` Chunk 40 for the full writeup (already covered there via the Chapter 3 addendum).

---

## Colours

### INS 150c / 150d — Caramel Colour Types III/IV
See `fssai_knowledge_base.md` Chunk 37 for the full 4-MEI/typing writeup. **Additional context recovered this pass, not yet folded into Chunk 37:** a widely-cited 2014 quantitative risk assessment (PLOS ONE / PMC) measured 4-MEI levels across 12 US beverages and found wide variation by brand and bottling location — Coca-Cola tested at the *lower* end of that range, not the higher end. EFSA's re-evaluation flagged 150d's dietary exposure as potentially exceeding the group ADI for adults at the 97.5th percentile, though not to the degree of concern raised for 150c. **This is a genuinely more scrutinized additive than most in this KB** — appropriate for [REGULATORY] or [UNCERTAIN] claim typing rather than [FACT] framing on any "is this safe" question, given real exposure-assessment ambiguity in the sources themselves.
**Source (additional):** EFSA, "Refined exposure assessment for caramel colours (E150a,c,d)," 2012; Vollmuth, "Caramel color safety – An update," Food and Chemical Toxicology 111 (2018); Cox et al., "Caramel Color in Soft Drinks and Exposure to 4-Methylimidazole: A Quantitative Risk Assessment," PLOS ONE/PMC, 2014.

### INS 160a(ii) — Beta-Carotene (Vegetable Source)
**Used in:** Real Fruit Power Mixed Fruit Juice.
**Regulatory status:** Permitted up to 200–1,000 mg/kg depending on category (200 mg/kg in non-carbonated water-based flavoured drinks, the relevant category here).
**Health considerations:** Among the most well-established and low-concern colourants in use — the same compound naturally present in the fruit. No meaningful safety concern at declared use levels. High *supplemental* (not dietary) beta-carotene intake has been studied re: smokers' lung cancer risk in unrelated contexts (CARET/ATBC trials) — no bearing on trace colourant use in a juice product.
**Source:** FSSAI Appendix A; well-established food-colourant literature (JECFA/EFSA consensus GRAS status).
**Metadata:** `{doc_type: "ingredient", entity: "Beta-Carotene (INS 160a(ii))", ins_no: "160a(ii)", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 160c — Paprika Oleoresin / Paprika Extract
**Note:** ⚠ Genuine regulatory gap.
**Used in:** Kurkure Masala Munch.
**Regulatory status:** **No match found** in Table 15 (Ready-to-eat savouries — Kurkure's category) and not on the GMP-blanket list either. A genuine coverage gap in the extracted dataset, not confidently a "not permitted" finding — either the specific permission exists in a part of Appendix A not captured for this category, or in a different FSSAI notification. Flag before making any regulatory claim about 160c in this product.
**Follow-up search this session:** same pattern as 334 and 472e — no source, primary or secondary, cites an FSSAI-specific mg/kg limit for 160c. All available numbers are international: JECFA's 79th report (2014) ADI of 0–1.5 mg/kg bw/day as total carotenoids, and EFSA's 2015 re-evaluation ADI of 24 mg/kg bw/day (or 1.7 mg carotenoids/kg bw/day). One relevant lead, not a confirmation: Codex's General Standard for Food Additives (GSFA) has adopted maximum permitted levels for 160c(ii) across 60+ international food categories — FSSAI's Appendix A structure is modeled on Codex's food category system (confirmed directly from the Appendix A front matter fetched this session), so a Codex-aligned entry may exist in Appendix A under a category-matching structure not surfaced by this reconstruction's searches. Worth checking Codex GSFA's savouries/snacks category directly as a next step, since FSSAI often mirrors it.
**Health considerations:** Internationally low-concern. JECFA and EFSA both found no genotoxicity concern. Unlike synthetic azo dyes, paprika extract has not been associated with hyperactivity or allergic-type reactions in sensitive individuals.
**2026-08-18 follow-up — real primary-source document read, still unresolved, now with a clear reason why:** obtained and directly read FSSAI's original 2011 Appendix A in full (via a state-government-hosted mirror, extracted with `pypdf`; the same document that resolved the DATEM entry above). 160c appears only in the document's "International Numbering System (INS) for Food Additives" identification index (INS number + name + generic function class, e.g. "44. 160c Paprika Oleoresins Colour") — this index is explicitly for naming/identification only ("The following list is only for identifying the food additive and their synonyms," per the document's own header), not category-specific limits. The document's 15 food-category tables (bread/biscuits, oils/fats, general food products, sugars/salt, confectionery/cocoa, milk products, cheese) do **not include a dedicated colours-by-category table at all** — so 160c's category-specific status genuinely cannot be determined from this document, for any category, not just savouries. This is a real document-coverage limitation, not a "not permitted" finding. A newer, Codex-realigned Appendix A version (referenced in FSSAI's current site structure but not successfully retrieved this session) likely contains the colour-limits tables this 2011 version lacks.
**Source:** JECFA 79th Report (2014); EFSA ANS Panel, "Scientific Opinion on the re-evaluation of paprika extract (E160c)," 2015; FSSAI Appendix A 2011 (confirmed additive exists in the regulatory system, no category-limit table available in this document version).
**Metadata:** `{doc_type: "ingredient", entity: "Paprika Oleoresin (INS 160c)", ins_no: "160c", source: "JECFA 2014 + EFSA 2015; FSSAI 2011 Appendix A checked 2026-08-18, no colour-limits table present in this document version", last_verified: "2026-08-18"}`

---

## Antioxidants

### INS 300 — Ascorbic Acid (Vitamin C)
**Used in:** Real Fruit Power Mixed Fruit Juice.
**Regulatory status:** Permitted at GMP levels in fruit juices (Table 14).
**Health considerations:** Essential nutrient, excellent safety record; concerns only arise in combination with sodium benzoate under specific storage/heat conditions (see INS 211) — worth cross-checking if a product contains both.
**Metadata:** `{doc_type: "ingredient", entity: "Ascorbic Acid / Vitamin C (INS 300)", ins_no: "300", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

### INS 307b — Mixed Tocopherols (Vitamin E)
**Used in:** Kellogg's Multigrain Chocos; Kellogg's Corn Flakes.
**Regulatory status:** Permitted up to 500 mg/kg in the relevant cereal category.
**Health considerations:** Essential nutrient; as a food antioxidant, one of the lowest-concern additives in common use.
**Metadata:** `{doc_type: "ingredient", entity: "Mixed Tocopherols / Vitamin E (INS 307b)", ins_no: "307b", source: "FSSAI Appendix A", last_verified: "2025-08-01"}`

---

## Sweeteners

### INS 950 — Acesulfame Potassium
**Used in:** Diet Coke.
**Regulatory status:** FSSAI-permitted, cross-reference WHO non-sugar-sweetener guideline already in `nutrition_knowledge_base.md` Chunk 8.
**Health considerations:** Extensive safety record with regulatory bodies worldwide; not metabolized by the body, excreted unchanged.
**Source:** FSSAI Appendix A; WHO "Non-sugar sweeteners" guideline (cross-reference, don't duplicate).
**Metadata:** `{doc_type: "ingredient", entity: "Acesulfame Potassium (INS 950)", ins_no: "950", source: "FSSAI Appendix A + WHO", last_verified: "2025-08-01"}`

### INS 951 — Aspartame

**Used in:** Diet Coke.
**Regulatory status:** FSSAI permits aspartame up to **700 ppm in carbonated beverages** specifically, under the Food Safety and Standards (Food Products Standards and Food Additives) Regulations, 2011 — same figure as `fssai_knowledge_base.md` Chunk 50, which is now the confirmed number for this category. **✅ RESOLVED 2026-08-18** (was flagged as a conflict against Chunk 50 during Phase 3 pipeline testing, 2026-08-13): the "600 mg/kg" figure previously stated here was a real regulatory number, but for the **wrong jurisdiction** — 600 mg/L (≈600 mg/kg for a water-based beverage) is the EU's aspartame limit under Regulation (EC) No. 1333/2008, not an FSSAI figure. It was mislabeled as FSSAI in this entry's original drafting. Verified against three independent secondary sources reporting the FSSAI 700ppm/carbonated-water figure consistently, and against the EU regulation number separately, to confirm neither the number nor the mix-up was a fabrication — this was a real jurisdiction confusion, not made up.
**Health considerations:** The most regulatory-scrutinized sweetener in this product set. In July 2023, **IARC (WHO's cancer research arm) classified aspartame as "possibly carcinogenic to humans" (Group 2B)** — the same category as many common exposures with limited evidence, reflecting *limited* evidence rather than a confirmed causal link. In the same announcement, **JECFA reaffirmed the existing ADI of 40 mg/kg body weight/day** — the expert nutrition/toxicology body did not lower the safe-intake threshold despite IARC's hazard classification. These are two different assessment types (hazard identification vs. risk/exposure assessment) frequently conflated in consumer reporting. Separately, aspartame is contraindicated for people with **phenylketonuria (PKU)** — metabolized to phenylalanine, well-established, the reason for PKU warnings on aspartame products in many markets.
**Source:** IARC Monograph, "Aspartame," July 2023; WHO/FAO JECFA statement accompanying the IARC classification, July 2023; FSSAI Food Product Standards, beverage standards chapter (carbonated beverages) — see `fssai_knowledge_base.md` Chunk 50 for the primary-source extraction this figure is confirmed against.
**Metadata:** `{doc_type: "ingredient", entity: "Aspartame (INS 951)", ins_no: "951", source: "IARC + JECFA 2023 + FSSAI beverage standards (confirmed 700ppm, matches Chunk 50)", last_verified: "2026-08-18"}`

---

## Flavour Enhancers

### INS 627 / 631 / 635 — Disodium 5'-Guanylate / Disodium 5'-Inosinate / Disodium 5'-Ribonucleotides
**Note:** ⚠ Genuine regulatory gap.
**Used in:** Yippee noodles; Maggi (flavour-enhancer group, commonly bundled with MSG in instant-noodle seasoning).
**Note on this entry's history:** this previously pointed to `fssai_knowledge_base.md`'s "Chunk 42" for the full writeup — that pointer was **broken**, discovered 2026-08-18. Chunk 42 actually covers sodium benzoate (INS 211), not this flavour-enhancer group; the referenced content never existed in `fssai_knowledge_base.md`. Content rewritten here directly rather than re-pointing to a still-missing chunk.
**Regulatory status:** FSSAI's original 2011 Appendix A (directly read 2026-08-18, same document that resolved the DATEM entry above) lists 627, 631, and 635 in its "International Numbering System (INS) for Food Additives" identification index — confirming they're recognized, named additives in the regulatory system, function class "flavour enhancer" — but that index is explicitly for identification/naming only, not category-specific limits. This document's 15 food-category tables don't include a dedicated flavour-enhancer-limits table covering instant noodles/seasoning, so **category-specific permission for this product type genuinely cannot be determined from this document** — same document-coverage limitation found for 160c above, not a "not permitted" finding.
**Health considerations:** Well-established flavour enhancers (the "umami" 5'-ribonucleotide family, commonly used alongside MSG). JECFA has evaluated this class and found no safety concern at typical dietary exposures; "not specified" (no numerical ADI limit needed) is JECFA's own classification for this group, reflecting very low toxicological concern rather than missing data.
**Source:** JECFA food additive evaluations (5'-ribonucleotide group, "ADI not specified"); FSSAI Appendix A 2011 (additives confirmed to exist in the regulatory system via the identification index; no category-limit table available in this document version for the relevant product category).
**Metadata:** `{doc_type: "ingredient", entity: "5'-Ribonucleotide flavour enhancers (INS 627/631/635)", ins_no: "627/631/635", source: "JECFA ADI-not-specified; FSSAI 2011 Appendix A checked 2026-08-18, no flavour-enhancer-limits table present in this document version", last_verified: "2026-08-18"}`

---

## Reconciliation with Tier 2 (resolved, not just flagged)
This file originally carried its own short "consolidated whole-food entries" list (sugar, iodised salt, refined wheat flour, milk solids, cocoa solids) and a batched spice list — both **removed from this file** in favor of `ingredient_kb_tier2.md`'s versions, which cover the same ingredients with broader detail (per-flour, per-oil, per-spice-category breakdowns) rather than a shorter high-recurrence cut. Tier 1 (this file) now contains **only** INS-numbered additives. All base/whole-food ingredient entries — including the ones with product-recurrence counts (sugar in 19 products, iodised salt in 15, etc.) — live in Tier 2. Don't maintain two independent lists for the same ingredient name; one was retired in this reconciliation pass to prevent exactly the kind of duplicate-chunk retrieval bug already caught once with the caramel colour merge.

**Also excluded from both tiers, deliberately:** "Vitamins/Minerals (Fortification Blend, Unspecified)" and "Mixed Spices / Spices & Condiments (Unspecified Blend)" — generic label placeholders, not identifiable single substances. Per-product fortification detail already lives in `products_compiled.json`'s `nutrition.fortification` block; don't recreate it here.

---

## Still not recovered in this reconstruction pass
A handful of entries from the original ~40-45 count weren't re-pulled (would be redundant with content already in `fssai_knowledge_base.md`, or genuinely minor): INS 621 (MSG — trunk Chunk 7 covers it), colours 150a/150b (basic caramel types, lower priority — no 4-MEI limit applies to either). If a gap surfaces later, these are the first place to look.
