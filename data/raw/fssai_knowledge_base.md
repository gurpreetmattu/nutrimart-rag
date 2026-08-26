# FSSAI Knowledge Base — COMPLETE MERGED FILE
**Status:** Single-file merge of the trunk (originally 29 chunks) + all 4 addenda (fats/oils, Chapter 3, session1, beverages/dairy/sauces), renumbered sequentially. This is the one file to upload to the Project, replacing anything currently there under this filename.

**Chunk count:** 50 chunks total (up from 45 — this pass recovered 5 more chunks that existed in past sessions but were never merged: Chunks 46-49 from the original sequencing-pushback session on Chapter 2.7, and Chunk 50, extracted from a primary-source beverage-standards PDF but never formally drafted into a chunk).

**Coverage:** preservatives, antioxidants, sweeteners, MSG, emulsifiers, anticaking, acidity regulators, synthetic colours, carry-over principle (general + infant-formula carve-out), INS/allergen/nutrition-panel/sweetener labelling (Version-VIII updated where superseded), 10 claims/advertising rules, vegetable oil/fat processing terms, fats/oils compositional standards, caramel colour 4-MEI typing, ADI/GMP, sweetener caloric classification, flavouring definitions, INS 551/223/211, flavour enhancers 627/631/635 (partial), and provisional beverages/dairy/sauces/fortification coverage.

**Sourcing tiers present in this file — pay attention to `source` and `last_verified` per chunk, not just chunk number:**
- **Primary, directly processed:** Chunks 1–41 (original gazette PDFs, Version-VIII consolidation, Chapter 2.2, Chapter 3)
- **Primary, fully verified:** Chunk 42 (sodium benzoate identity AND category limit both confirmed 2026-08-18, see Finding 14/15 in `PHASE3_TESTING_LOG.md`) — INS 627/631/635 has no chunk in *this file*; see `ingredient_knowledge_base.md`'s own entry instead (a stale pointer to this file was found and fixed 2026-08-18, see `PHASE3_TESTING_LOG.md` Finding 13)
- **Secondary, explicitly provisional:** Chunks 43–45, 47 (beverages/dairy/fortification/health-drink labelling) — flagged for primary-source verification before production use. Chunk 45's ketchup-preservative figure is the exception — now confirmed (2026-08-18); its compositional-standard content (TSS/acidity) is still provisional.

**Known remaining content gap:** the 750ppm sodium-benzoate figure (Chunk 42) is now confirmed against FSSAI Appendix A Table 10 (2026-08-18) — no longer a gap. INS 627/631/635's status is covered in `ingredient_knowledge_base.md`, not here (2026-08-18: directly checked against FSSAI's 2011 Appendix A — confirmed as a real, named additive, but no category-limit table exists in that document version for the relevant product category).

**Source PDFs:**
- FSSAI, "Food Safety and Standards (Food Products Standards and Food Additives) Regulations, 2011" — Chapter 3 ("Substances Added to Food"), pp.417–435
- FSSAI, "Food Safety and Standards (Labelling and Display) Regulations, 2020" — original gazette, 14/12/2020
- FSSAI, "...Labelling and Display Regulations, 2020 — Consolidated, Version-VIII (09.09.2025)" — same regulation as above, consolidated with amendments through Aug 2025. **Supersedes the 2020 text wherever they conflict.** Chunks 14, 15, 16 updated to V8 text; Chunk 17 is new in V8.
- FSSAI, "Food Safety and Standards (Advertising and Claims) Regulations, 2018" — Chunks 18–27

**doc_type split:** `regulatory` (Chunks 1–17) answers "is this substance/level permitted." `claims_advertising` (Chunks 18–27) answers "is this marketing phrase/claim legally supportable." Kept as separate `doc_type` values deliberately — same source authority (FSSAI) but different retrieval intent; merging them risks cross-contaminated retrieval (a preservative-ppm query surfacing a "traditional" branding rule, or vice versa).

**Scoping note:** Scoped to additive classes, label declarations, and claim rules plausible for a packaged snack/namkeen/biscuit-type product catalog — not the full source documents. Chapter 3.2 of the Additives Regulations (colour purity/chemical-assay specs — manufacturer QC, not consumer-facing) was deliberately excluded, as was the bulk of the Labelling Regulations unrelated to ingredients/nutrition/allergens (net quantity, principal-display-panel sizing, imported-food rules).

---

## Chunk 1
**Topic:** Preservatives — Classification and General Rule

**Definition:** A preservative is a substance that inhibits, retards, or arrests fermentation, acidification, or other decomposition of food.

**Classification:**
- **Class I** (unrestricted use): common salt, sugar, dextrose, glucose syrup, spices, vinegar/acetic acid, honey, edible vegetable oils.
- **Class II** (restricted, product-specific ppm limits apply — see Chunk 2): benzoic acid and its salts, sulphurous acid and its salts (sulphur dioxide), sodium/potassium nitrate or nitrite, sorbic acid and its sodium/potassium/calcium salts, sodium/calcium propionate, methyl/propyl parahydroxybenzoate, propionic acid and its esters/salts, sodium diacetate, lactic acid salts, nisin.

**Key rule:** Only **one** Class II preservative may be used in a food unless the regulation explicitly allows alternatives "in the alternative" for that food category — in which case combinations are permitted, but each preservative's share must be proportionally reduced.

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.4(1)–(2), p.424.
**Last verified:** 2011 (original notification)
**Metadata:** `{doc_type: "regulatory", entity: "preservatives_general", regulation: "FSS_Additives_2011", source: "FSSAI"}`

---

## Chunk 2
**Topic:** Preservatives — Sulphur Dioxide & Benzoic Acid Permitted Limits (Product-Specific)

**Applies to product categories relevant to packaged snacks:**
- Sauces, chutneys, pickles: Benzoic acid up to 750 ppm (tomato/other sauces), 250 ppm or sulphur dioxide 100 ppm (pickles/chutneys from fruit or vegetables).
- Jam, marmalade, preserve, fruit jelly: sulphur dioxide 40 ppm OR benzoic acid 200 ppm.
- Fruit syrups, squashes, crushes, cordials, non-alcoholic wines: sulphur dioxide 350 ppm OR benzoic acid 600 ppm.
- Ready-to-serve beverages: sulphur dioxide OR benzoic acid, 70 ppm / 120 ppm respectively.
- Corn flour and similar starches: sulphur dioxide 100 ppm.
- Dried fruits: sulphur dioxide 750–2000 ppm depending on fruit type.
- Refined sugar: sulphur dioxide 40 ppm; plantation white sugar/jaggery/misri: 70 ppm.

**Mixed-food rule:** if two foods each carrying a permitted preservative are combined, the Class II preservative limit in the mixture is the weighted average based on the proportion of each component food.

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.4(3)–(4), Table, pp.424–427.
**Last verified:** 2011 (original notification)
**Metadata:** `{doc_type: "regulatory", entity: "sulphur_dioxide_benzoic_acid", regulation: "FSS_Additives_2011", source: "FSSAI"}`

---

## Chunk 3
**Topic:** Preservatives — Sorbic Acid / Potassium Sorbate Limits

**Applies to:** Cheese/processed cheese (3000 ppm), flour confectionery (1500 ppm), preserved chapatis (1500 ppm), paneer/channa (2000 ppm sorbic acid or 2000 ppm propionic acid), fat spread (1000 ppm sorbic acid or 1000 ppm benzoic acid), jams/jellies/marmalades/candied fruit (500 ppm), fruit juice concentrates (100 ppm), bottled/canned fruit juices (200 ppm), prunes (potassium sorbate 1000 ppm).

**Relevance:** Sorbic acid / potassium sorbate is one of the most common preservatives declared on Indian packaged snack and bakery labels (INS 200–203).

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.4(3), Table items 31–45, pp.426–427.
**Last verified:** 2011 (original notification)
**Metadata:** `{doc_type: "regulatory", entity: "sorbic_acid", regulation: "FSS_Additives_2011", source: "FSSAI"}`

---

## Chunk 4
**Topic:** Anti-oxidants — Permitted Substances and Limits

**Default rule:** No antioxidant other than lecithin, ascorbic acid, and tocopherol may be added to any food unless separately permitted.

**Additional antioxidants permitted in edible oils/fats (excl. ghee & butter):** ethyl/propyl/octyl/dodecyl gallate (0.01% combined), ascorbyl palmitate (0.02%), BHA (0.02%), citric/tartaric/gallic acid (0.01%), resin guaiac (0.05%), TBHQ (0.02%).

**Category-specific carve-outs (relevant to packaged snacks):**
- Ready-to-eat dry breakfast cereals: BHA up to 0.005% (50 ppm) — notably tighter than the general 0.02% oil/fat limit.
- Chewing gum/bubble gum: BHA up to 250 ppm.
- Fat spread: BHA or TBHQ up to 0.02% by weight on a fat basis.
- Where BHA is combined with gallates, the combined mixture still may not exceed 0.02%.

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.5, pp.427–428.
**Last verified:** 2011 (original notification)
**Metadata:** `{doc_type: "regulatory", entity: "antioxidants_BHA_TBHQ", regulation: "FSS_Additives_2011", source: "FSSAI"}`

---

## Chunk 5
**Topic:** Artificial (Non-Nutritive) Sweeteners — Permitted List, Limits, and Mixing Rules

**Permitted sweeteners:** Saccharin Sodium, Aspartame, Acesulfame Potassium, Sucralose, Neotame — each with product-specific ppm ceilings (e.g. sugar-free confectionery 3500 ppm sucralose; chewing/bubble gum 5000 ppm; carbonated water 300 ppm sucralose or 33 ppm neotame; biscuits/breads/cakes 750 ppm sucralose).

**Mixing rule:** No mixture of artificial sweeteners is allowed in general food products; only a few named exceptions (carbonated water: sucralose + acesulfame-K proportionally; table-top sweetener: aspartame + acesulfame-K fixed 2:1) permit combination.

**Aspartame-specific caution:** Foods containing aspartame must carry "NOT FOR PHENYLKETONURICS."

**Relevance:** Complements the WHO non-sugar-sweetener guidance in `nutrition_knowledge_base.md` Chunk 8 — that chunk covers *why*; this covers *what's legally permitted at what level*.

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.3, pp.420–423.
**Last verified:** 2011 (original notification)
**Metadata:** `{doc_type: "regulatory", entity: "artificial_sweeteners", regulation: "FSS_Additives_2011", source: "FSSAI", comparison_group: "sugar_vs_sweetener"}`
**2026-08-18 note:** tagged with `comparison_group` to pair with `nutrition_knowledge_base.md` Chunk 8c — real pairing verified via live retrieval, not a guess: for q07-style "should I pick the diet version" queries, this chunk and Chunk 8c both reach the fused candidate pool but neither individually clears the corrective-retry confidence threshold; together they answer the comparison. See `PHASE3_TESTING_LOG.md` for the Finding this fixes.

---

## Chunk 6
**Topic:** Polyols & Polydextrose — Permitted Use and the "May Have Laxative Effect" Trigger

**Guidance:** Isomalt, erythritol, and maltitol/maltitol syrup may be used at GMP levels in bakery products, ice cream/frozen dessert, jams/jellies, and traditional Indian sweets. Polydextrose likewise at GMP levels in similar categories.

**Mandatory label trigger:** If a product contains **10% or more polyols** or **10% or more polydextrose**, the label must carry "Polyols may have laxative effect" or "Polydextrose may have laxative effect" respectively.

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.3(4)–(5), pp.423–424; label trigger cross-referenced from FSSAI, Labelling and Display Regulations, 2020, Schedule-II §1(1) items 1–2, p.43.
**Last verified:** 2011 / 2020
**Metadata:** `{doc_type: "regulatory", entity: "polyols_polydextrose", regulation: "FSS_Additives_2011,FSS_Labelling_2020", source: "FSSAI"}`

---

## Chunk 7
**Topic:** Flavour Enhancer — Monosodium Glutamate (MSG)

**Permitted use:** MSG may be added at GMP levels to foods listed in Appendix A of the Additives Regulations, with mandatory label declaration.

**Prohibited in:** Infant food, foods for children under 12 months, fresh/frozen fruit & vegetables, flours of cereals/pulses/starches, dried pasta and noodles, bread, sugar confectionery, chocolate, plain milk-based and dairy products. MSG *is* permitted in most savoury snack, seasoning, and instant-noodle-seasoning categories.

**Mandatory label declaration:** "This package of (name of food) contains added MONOSODIUM GLUTAMATE — NOT RECOMMENDED FOR INFANTS BELOW 12 MONTHS AND PREGNANT WOMEN."

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.11, pp.431–432; label text from FSSAI, Labelling and Display Regulations, 2020, Schedule-II §1(4) item 4, p.44.
**Last verified:** 2011 / 2020
**Metadata:** `{doc_type: "regulatory", entity: "msg_monosodium_glutamate", regulation: "FSS_Additives_2011,FSS_Labelling_2020", source: "FSSAI"}`

---

## Chunk 8
**Topic:** Emulsifying & Stabilising Agents — Snack-Relevant Substances and Limits

**General list:** agar, alginic acid, calcium/sodium alginates, carrageenan, edible gums (guar, karaya, arabic, gum ghatti), dextrin, sorbitol, pectin, lecithin, gelatin, modified starches, mono-/diglycerides of fatty acids, sodium/calcium stearoyl-2-lactylate.

**Snack/bakery-specific limits:**
- Modified food starches: up to 0.5% in confectionery/dairy/sauces/soups; **up to 5% in snacks, frozen potato products, baked foods, and salad dressing/mayonnaise.**
- HPMC: up to 1.0% in snacks/savouries/instant mixes; 2.0% in non-dairy whip topping.
- Xanthan gum: up to 0.5% in bakery mixes and non-dairy whip toppings.
- Polyglycerol esters of fatty acids: up to 0.2% in bakery products and chocolate.

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.6, pp.428–430.
**Last verified:** 2011 (original notification)
**Metadata:** `{doc_type: "regulatory", entity: "emulsifiers_stabilisers", regulation: "FSS_Additives_2011", source: "FSSAI"}`

---

## Chunk 9
**Topic:** Anticaking Agents — Restricted Use

**Rule:** Anticaking agents are prohibited except where specifically permitted. Table salt, onion powder, garlic powder, fruit powder, and soup powder may contain carbonates/phosphates/silicates of calcium/magnesium/sodium, or myristates/palmitates/stearates of aluminium/ammonium/calcium/potassium/sodium, up to 2.0% singly or combined.

**Special case:** Calcium, potassium, or sodium ferrocyanide may be used as a crystal modifier/anticaking agent specifically in common salt, iodised salt, and iron-fortified salt, capped at 10 mg/kg (as ferrocyanide).

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.7, p.430.
**Last verified:** 2011 (original notification)
**Metadata:** `{doc_type: "regulatory", entity: "anticaking_agents", regulation: "FSS_Additives_2011", source: "FSSAI"}`

---

## Chunk 10
**Topic:** Sequestering & Buffering Agents (Acidity Regulators)

**Definition:** Sequestering agents chelate trace metals to prevent oxidative rancidity/off-taste/decolourisation; buffering agents counter acidic/alkaline shifts during storage or processing.

**Common substances relevant to snacks/beverages:** citric acid & malic acid (GMP, carbonated beverages and miscellaneous foods), phosphoric acid (600 ppm, beverages/soft drinks), lactic acid (GMP, miscellaneous foods — DL-lactic acid and L(+)-tartaric acid prohibited in food for children under 12 months), calcium carbonate (10,000 ppm as a general neutraliser).

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.12, Table, pp.432–433.
**Last verified:** 2011 (original notification)
**Metadata:** `{doc_type: "regulatory", entity: "sequestering_buffering_agents", regulation: "FSS_Additives_2011", source: "FSSAI"}`

---

## Chunk 11
**Topic:** Synthetic Food Colours — Permitted List and Category Restrictions

**Permitted synthetic colours (only these, no others):** Ponceau 4R, Carmoisine, Erythrosine (reds); Tartrazine, Sunset Yellow FCF (yellows); Indigo Carmine, Brilliant Blue FCF (blues); Fast Green FCF (green).

**Category restriction:** Relevant permitted categories for this catalog: biscuits (incl. wafer), pastries, cakes, confectionery, thread candies, sweets, and specific savouries (dalmoth, mongia, phululab, sago papad, dal biji only — most namkeen/savoury snacks are *not* on the permitted-colour list). Ice cream, milk lollies, frozen desserts, flavoured milk, and yoghurt are also permitted categories.

**Lake colour specific limit:** Aluminium Lake of Sunset Yellow FCF capped at 0.04% by weight in powdered beverage mix.

**Natural colours** (carotene/carotenoids, chlorophyll, riboflavin, caramel, annatto, saffron, curcumin/turmeric) permitted more broadly without the same category restriction.

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.2, pp.418–419.
**Last verified:** 2011 (original notification)
**Metadata:** `{doc_type: "regulatory", entity: "synthetic_food_colours", regulation: "FSS_Additives_2011", source: "FSSAI"}`

---

## Chunk 12
**Topic:** The "Carry-Over" Principle

**Rule:** An additive present in a finished food solely because it was already present in a raw material/ingredient used to make that food is permissible **without separate approval for that food category**, provided the total amount — including the carry-over — doesn't exceed the maximum otherwise permitted. Contaminants aren't covered.

**Relevance:** Check this exception before flagging an additive as a compliance issue for a category it isn't separately "permitted" in.

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Reg. 3.1.18, p.435.
**Last verified:** 2011 (original notification)
**Metadata:** `{doc_type: "regulatory", entity: "carry_over_principle", regulation: "FSS_Additives_2011", source: "FSSAI"}`

---

## Chunk 13
**Topic:** Food Additive Declaration on Label

**Rule:** Food additives must be declared in the ingredient list with either their specific name or the INS number, together with their functional class (e.g. "Preservative (INS 211)"). Artificial flavours require the common name; natural/nature-identical flavours only require the class name "flavour."

**Source:** FSSAI, Labelling and Display Regulations, 2020, Reg. 5(5), p.35.
**Last verified:** 2020-12-14
**Metadata:** `{doc_type: "regulatory", entity: "additive_ins_declaration", regulation: "FSS_Labelling_2020", source: "FSSAI"}`

---

## Chunk 14
**Note:** Updated to Version-VIII, 09.09.2025.
**Topic:** Allergen Declaration Requirements

**Rule:** Eight allergen categories must be declared separately as "Contains: [name]" whenever present: cereals containing gluten (wheat, rye, barley, oats, spelt), crustaceans, milk & milk products, eggs, fish, peanuts & tree nuts, soybeans, and sulphites at ≥10 mg/kg. Cross-contamination risk may optionally be declared as "May Contain: [name]."

**Exemptions — broadened by Version-VIII (not present in the original 2020 text):**
- Wheat-based glucose syrups (incl. dextrose) and wheat-based maltodextrins, glucose syrups based on barley, and cereals used to make alcoholic distillates (incl. agricultural ethyl alcohol) are exempt from the "Contains: wheat/barley" declaration — if assessed as safe and residual gluten is below 20 mg/kg.
- **Oils AND distilled alcoholic beverages** derived from an allergen are both exempt (original 2020 exempted only oils) — but only where the product itself isn't the allergen food.
- Raw agricultural commodities remain exempt entirely.

**Source:** FSSAI, Labelling and Display Regulations, 2020 (Version-VIII, 09.09.2025), Reg. 5(14), pp.18–19.
**Last verified:** 2025-09-09
**Metadata:** `{doc_type: "regulatory", entity: "allergen_declaration", regulation: "FSS_Labelling_2020_v8", source: "FSSAI", superseded_by: null}`

---

## Chunk 15
**Note:** Updated to Version-VIII, 09.09.2025.
**Topic:** Nutritional Information Panel — Definitions and India RDA Basis

**Required fields per 100g/100ml or per serve, plus %RDA:** energy (kcal), protein (g), carbohydrate (g) with total sugars (g) and added sugars (g), total fat (g) with saturated fat (g), trans fat (g), and cholesterol (mg), sodium (mg).

**India's RDA calculation basis (2000 kcal/day reference):** total fat 67g, saturated fat 22g, trans fat 2g, added sugar 50g, sodium 2000mg (5g salt).

**Tolerance:** Declared nutrient values may vary up to −10% from the label value at any point within shelf life.

**Exemptions:** single-ingredient unprocessed foods, salt, herbs/spices/curry powder (except direct-consumption sprinkler masala), plain tea/coffee, chewing gum and bubble gum, alcoholic beverages.

**Version-VIII conditional-field amendment:**
- Saturated fat and trans fat need only be declared if total fat content **exceeds 0.5%**.
- Cholesterol need only be declared for products **containing fats of animal origin, and only where total fat exceeds 0.5%** — most plant-oil-fried namkeen/chips (no animal fat) don't require a cholesterol figure at all, regardless of fat content.

**Source:** FSSAI, Labelling and Display Regulations, 2020 (Version-VIII, 09.09.2025), Reg. 5(3), pp.9–12.
**Last verified:** 2025-09-09
**Metadata:** `{doc_type: "regulatory", entity: "nutrition_panel_rda_india", regulation: "FSS_Labelling_2020_v8", source: "FSSAI"}`

---

## Chunk 16
**Note:** Substantially expanded in Version-VIII — treat the 2020-only version as stale.
**Topic:** Non-Nutritive Sweetener & Caffeine Warning Labels (Consumer-Facing)

**What changed:** the 2020 rule had one generic warning for any artificial sweetener. Version-VIII gives **per-sweetener** warning text.

**Sweeteners and required warnings:**
- **Aspartame:** "Not recommended for phenylketonurics; for children suffering from seizure disorders; pregnant and lactating mothers."
- **Acesulfame Potassium:** "Not recommended for children; pregnant and lactating mothers."
- **Aspartame-Acesulfame salt:** "Not recommended for phenylketonurics; for children; pregnant and lactating mothers."
- **Saccharins:** "Not recommended for children."
- **Sucralose, Neotame, Steviol Glycoside:** listed but without the population-specific warning language above.
- **Polyols (as sweetener):** "Polyols may have laxative effect."
- **Sorbitol/Sorbitol syrup (as sweetener):** see Chunk 17.

**Every sweetener-containing product must also state:** "Contains [name of sweetener], with purity and weight percent of the marker compound." A mixture requires an admixture statement naming all of them, plus each individual warning.

**Caffeine:** unchanged — "CONTAINS CAFFEINE" + ppm quantity in the ingredient list.

**Pan masala:** unchanged text, but Version-VIII adds a size rule: the warning must cover **50% of the front-of-pack**.

**Source:** FSSAI, Labelling and Display Regulations, 2020 (Version-VIII, 09.09.2025), Schedule-II §1(1) items 3–4, §1(3) items 1–3, §1(4) items 1–4, pp.27–31.
**Last verified:** 2025-09-09
**Metadata:** `{doc_type: "regulatory", entity: "sweetener_caffeine_warnings", regulation: "FSS_Labelling_2020_v8", source: "FSSAI"}`

---

## Chunk 17
**Note:** New in Version-VIII — did not exist in the 2020 original.
**Topic:** Sorbitol / Sorbitol Syrup — Mandatory Warning Trigger

**Rule:** Where a product contains **10% or more Sorbitol and/or Sorbitol syrup**, the label must carry: **"May have laxative effect, cause bloating and diarrhea in children; and reduce calcium absorption in post-menopausal women."**

**Relevance:** Sits alongside the generic polyol 10%-trigger in Chunk 6 — Sorbitol is itself a polyol, but gets its own more detailed warning. If a product's ingredient list shows Sorbitol specifically, use this text over the generic polyol one.

**Source:** FSSAI, Labelling and Display Regulations, 2020 (Version-VIII, 09.09.2025), Schedule-II §1(1) item 5, p.29.
**Last verified:** 2025-09-09
**Metadata:** `{doc_type: "regulatory", entity: "sorbitol_warning", regulation: "FSS_Labelling_2020_v8", source: "FSSAI"}`

---

## Chunk 18
**Topic:** Nutrition Claims — Energy, Fat & Cholesterol Thresholds ("Low"/"Free")

**Energy/Calorie:** Low ≤40 kcal/100g (solids) or ≤20 kcal/100ml (liquids); Free ≤4 kcal/100ml.
**Fat (total):** Low ≤3g/100g or ≤1.5g/100ml; Free ≤0.5g/100g/100ml.
**Cholesterol:** Low ≤20mg/100g solids (+ ≤1.5g sat fat/100g, sat fat ≤10% energy) or ≤10mg/100ml liquids (+ ≤0.75g sat fat/100ml, same cap); Free ≤5mg/100g/100ml plus same sat-fat conditions as Low.

**Source:** FSSAI, Advertising and Claims Regulations, 2018, Schedule I items 1–3, pp.26–27.
**Last verified:** 2018 (original notification)
**Metadata:** `{doc_type: "claims_advertising", entity: "energy_fat_cholesterol_claims", regulation: "FSS_Claims_2018", source: "FSSAI"}`

---

## Chunk 19
**Topic:** Nutrition Claims — Saturated Fat, Trans Fat & Unsaturated Fat Thresholds

- **Saturated fat — Low:** ≤1.5g/100g or ≤0.75g/100ml, AND ≤10% of energy. **Free:** ≤0.1g/100g/100ml.
- **Trans fat — Free:** <0.2g/100g/100ml.
- **Unsaturated fat — High:** ≥70% of total fatty acids unsaturated AND >20% of energy.
- **MUFA — High:** ≥45% of fatty acids AND >20% of energy. **PUFA — High:** ≥45% AND >20% of energy.
- **Omega-3 — Source:** ≥0.3g ALA/100g and /100kcal, OR ≥40mg EPA+DHA/100g and /100kcal. **High:** double those.

**Note:** the Trans Fat "Free" claim threshold (<0.2g/100g) is a *marketing-claim* bar, distinct from the mandatory nutrition-panel trans-fat *disclosure* rule (Chunk 15) — a product can be required to disclose trans fat without being eligible to say "Trans Fat Free."

**Source:** FSSAI, Advertising and Claims Regulations, 2018, Schedule I items 4–9, pp.26–27.
**Last verified:** 2018 (original notification)
**Metadata:** `{doc_type: "claims_advertising", entity: "fat_type_claims", regulation: "FSS_Claims_2018", source: "FSSAI"}`

---

## Chunk 20
**Topic:** Nutrition Claims — Sugar Thresholds ("Low"/"Free")

- **Low:** ≤5g sugars/100g or ≤2.5g/100ml. **Free:** ≤0.5g/100g/100ml.

**Relevance:** Much stricter than WHO's ~10%-of-energy daily *intake* guidance in the general nutrition sub-base — this is a marketing-claim threshold, checkable directly against structured nutrition data.

**Source:** FSSAI, Advertising and Claims Regulations, 2018, Schedule I item 10, p.27.
**Last verified:** 2018 (original notification)
**Metadata:** `{doc_type: "claims_advertising", entity: "sugar_claims", regulation: "FSS_Claims_2018", source: "FSSAI"}`

---

## Chunk 21
**Topic:** Nutrition Claims — Sodium Thresholds

- **Low:** ≤0.12g/100g/100ml. **Very low:** ≤0.04g. **Sodium free:** ≤0.005g.

**Relevance:** Packaged namkeen/savoury snacks are typically sodium-heavy — most of the catalog is unlikely to meet these thresholds.

**Source:** FSSAI, Advertising and Claims Regulations, 2018, Schedule I item 13, p.27.
**Last verified:** 2018 (original notification)
**Metadata:** `{doc_type: "claims_advertising", entity: "sodium_claims", regulation: "FSS_Claims_2018", source: "FSSAI"}`

---

## Chunk 22
**Topic:** Nutrition Claims — Protein, Vitamin/Mineral & Fibre Thresholds

- **Protein — Source:** ≥10% RDA/100g / ≥5% RDA/100ml / ≥5% RDA/100kcal. **Rich/High:** double.
- **Vitamin(s)/Mineral(s) — Source:** ≥15% RDA/100g or ≥7.5% RDA/100ml. **High:** ≥30%/≥15%.
- **Dietary fibre — Source:** ≥3g/100g or ≥1.5g/100kcal. **High/Rich:** ≥6g/100g or ≥3g/100kcal.
- **Probiotics — Source:** ≥10⁸ CFU in the recommended daily serving.
- **Glycemic Index — Low GI:** below 55 (vs. white bread reference).

**Caveat:** "Source"/"High" protein and fat claims also require the nutrient to provide the specified minimum share of total energy — the raw gram/RDA figure alone isn't sufficient.

**Source:** FSSAI, Advertising and Claims Regulations, 2018, Schedule I items 11–16 + footnote, pp.27–28.
**Last verified:** 2018 (original notification)
**Metadata:** `{doc_type: "claims_advertising", entity: "protein_vitamin_fibre_claims", regulation: "FSS_Claims_2018", source: "FSSAI"}`

---

## Chunk 23
**Topic:** Nutrient Comparative Claims — Rules for "Reduced," "Less," "More"

**Rule:** Comparative claims must compare against a genuinely similar/equivalent food, and:
- Energy/macronutrient/sodium: relative difference ≥25%, and also meet the absolute "Low"/"Source" threshold from Chunks 18–22.
- Micronutrients other than sodium: difference ≥10% of RDA.

The identity of the compared food and size of the difference must be stated close to the claim — a bare "25% less sugar!" without naming what it's less than is non-compliant.

**Equivalence claims** ("as much fibre as an apple") are permitted only if the reference food would itself qualify as a "source" of that nutrient.

**Source:** FSSAI, Advertising and Claims Regulations, 2018, Reg. 5(4)–(6), pp.22–23.
**Last verified:** 2018 (original notification)
**Metadata:** `{doc_type: "claims_advertising", entity: "comparative_claims", regulation: "FSS_Claims_2018", source: "FSSAI"}`

---

## Chunk 24
**Topic:** Non-Addition Claims — "No Added Sugar" / "No Added Salt" / "No Added [Additive]"

**"No added sugar" requires ALL of:** (a) no sugars added directly, (b) no ingredient used that itself contains sugars (jam, sweetened chocolate, sweetened dried fruit), (c) no ingredient functioning as a sugar substitute (concentrated fruit juice, dried fruit paste), (d) no other means of raising the food's own sugar content (e.g. enzymatic starch hydrolysis). If sugars are naturally present despite meeting all four, must additionally state "CONTAINS NATURALLY OCCURRING SUGARS."

**"No added salt" requires:** no salt added directly, AND no ingredient used that itself contains added salt (sauces, pickles, pepperoni, soy sauce, fish sauce explicitly named as disqualifying).

**"No added [additive]" requires:** not added directly, not present via any ingredient, is one that's actually permitted for that category under the 2011 Additives Regs, and no substitute additive achieving the same function.

**Source:** FSSAI, Advertising and Claims Regulations, 2018, Reg. 6(1)–(3), pp.22–23.
**Last verified:** 2018 (original notification)
**Metadata:** `{doc_type: "claims_advertising", entity: "non_addition_claims", regulation: "FSS_Claims_2018", source: "FSSAI"}`

---

## Chunk 25
**Topic:** Health Claims — Structure and the Pre-Approved Claim Statements (Schedule III)

**Structural requirement:** every health claim needs (1) the nutrient/substance's physiological role or accepted diet-health relationship, and (2) the product's actual composition relevant to that role. Must be framed as part of a balanced diet, state quantity per serving, and name target groups/max safe intake where relevant.

**Pre-approved claim-relationship pairs (Schedule III):**
| Relationship | Condition | Approved statement |
|---|---|---|
| Calcium (± Vit D) & osteoporosis | source/high in calcium | "Adequate Calcium intake... essential for bone health and to reduce the risk of osteoporosis" |
| Sodium & hypertension | low sodium (≤0.12g/100g) | "Diets low in sodium may help in reducing the risk of high blood pressure" |
| Saturated fat & blood cholesterol | low saturated fat | "Diets low in saturated fat contribute to the maintenance of normal blood cholesterol levels" |
| Potassium & blood pressure | good source of potassium + low sodium/fat/sat-fat | "...may help reduce the risk of high blood pressure" |
| ALA (omega-3) & cholesterol | ≥1g omega-3/100g, daily intake 2g ALA | "...contributes to the maintenance of normal blood cholesterol levels" |
| Soluble fibre (oats/barley/millets) & lipid profile | ≥1g/serving, daily intake 3g | "...may help in the maintenance of normal lipid profile" |
| Phytosterol/stanol & lipid profile | ≥1g/serving, daily intake up to 3g | "...may help in improving the lipid profile" |
| Beta-glucans (oats/barley) & blood glucose | ≥4g per 30g available carbs | "...may help in reduction of rise in blood glucose after that meal" |

**Reduction-of-disease-risk claims** outside this list require prior FSSAI approval with formal scientific submission.

**Source:** FSSAI, Advertising and Claims Regulations, 2018, Reg. 7, Schedule III, pp.23–24, 28–29.
**Last verified:** 2018 (original notification)
**Metadata:** `{doc_type: "claims_advertising", entity: "health_claims", regulation: "FSS_Claims_2018", source: "FSSAI"}`

---

## Chunk 26
**Topic:** Prohibited & Restricted Claims

**Absolutely prohibited:** claims a food prevents/treats/cures disease (unless specifically permitted elsewhere); "recommended by medical professionals" wording; "added nutrients" claims where addition merely restores processing losses; health claims for foods whose other nutrient levels raise disease risk; claims casting doubt on other foods' safety or undermining competitors; meal-replacement positioning unless specifically permitted; using the FSSAI logo/license number as a promotional device.

**General principles:** every claim must be truthful, unambiguous, not encourage excess consumption, not imply a balanced diet is insufficient alone, specify servings/day where relevant, and be scientifically substantiated.

**Source:** FSSAI, Advertising and Claims Regulations, 2018, Reg. 4, 10, pp.21–22, 24.
**Last verified:** 2018 (original notification)
**Metadata:** `{doc_type: "claims_advertising", entity: "prohibited_claims", regulation: "FSS_Claims_2018", source: "FSSAI"}`

---

## Chunk 27
**Topic:** Restricted Marketing Words — "Natural," "Fresh," "Pure," "Traditional," "Original," "Authentic/Genuine/Real"

- **"Natural":** only for a single food from a recognised source, nothing added, minimal processing only. A composite food can't be "natural" itself — at most "made from natural ingredients," only if every ingredient qualifies. "Natural goodness"/"nature's way" banned outright.
- **"Fresh":** only if unprocessed beyond washing/peeling/chilling/trimming/cutting or low-dose irradiation (≤1kGy); any shelf-life-extending processing disqualifies it.
- **"Pure":** only for a single-ingredient food, nothing added, contamination below FSS Contaminants Regs limits. Composite food: "made with pure ingredients" at most.
- **"Traditional":** recipe/formulation/processing method demonstrably unchanged for at least **30 years**.
- **"Original":** origin traceable and materially unchanged, no major-ingredient substitutions, remains the standard product when variants launch.
- **"Authentic"/"Genuine"/"Real":** only if the label/ad also explains specifically, tangibly, in what way the claimed quality is justified.

**Brand-name disclaimer trigger:** if a brand/trade name contains one of these words in a way likely to mislead, the label must carry, in ≥3mm text: "*This is only a brand name or trade mark and does not represent its true nature."

**Relevance:** Highly applicable to Indian snack branding — "traditional namkeen," "authentic recipe," "original masala" are common phrasing in this exact product category.

**Source:** FSSAI, Advertising and Claims Regulations, 2018, Reg. 4(7), 9(2), Schedule V, pp.21, 24, 29–30.
**Last verified:** 2018 (original notification)
**Metadata:** `{doc_type: "claims_advertising", entity: "restricted_marketing_words", regulation: "FSS_Claims_2018", source: "FSSAI"}`

---

## Chunk 28
**Note:** New source: amended/consolidated Chapter 1, not previously in this file.
**Topic:** Regulatory Definitions — Vegetable Oil & Fat Processing Terminology

**Source note:** this chunk comes from a separately-uploaded, amended consolidation of Chapter 1 ("General") of the Additives Regulations, 2011 — distinct from the unamended `Food_Additives_Regulations.pdf` used for Chunks 1–17 (whose Chapter 1 was never chunked; only its Chapter 3 was used). **Second, independent instance of regulatory version drift**, separate from the Version-VIII labelling drift in Chunks 14–17: the amendment markers in this source go at least as high as "77," and several original definitions (mostly milk/dairy terms — "Double Toned Milk," "Full Cream Milk," "Flavoured Milk") were removed by amendment marker "38," presumably relocated into dairy-specific standards. Unlike Chunks 14–17, this source states **no clean consolidation date** — `last_verified` below is necessarily vaguer than elsewhere in this file.

**Definitions relevant to this catalog's ingredient lists:**
- **Hydrogenation:** the process of adding hydrogen to an edible vegetable oil using a catalyst, to produce a fat with semi-solid consistency. This is the formal definition behind "hydrogenated vegetable oil" / "partially hydrogenated oil" on ingredient lists, and the direct source of industrial trans fat (cross-reference: `nutrition_knowledge_base.md` Chunk 4b covers the WHO trans-fat health guidance; this chunk covers the process that creates it).
- **Refined vegetable oil:** oil obtained by expression or solvent extraction, then deacidified (with alkali, and/or physical refining, and/or miscella refining using permitted solvents), degummed (using phosphoric/citric acid and/or a food-grade enzyme), bleached (with adsorbent earth and/or activated carbon), and deodorized with steam — no other chemical agents used.
- **Refining:** the deacidification process itself — by alkali, physical refining, or miscella refining, optionally including degumming.
- **Raw edible oils:** oil obtained purely by mechanical means (expelling/pressing, with or without heat), optionally purified by washing/settling/filtering/centrifuging — **no processing aid may be used.** Still fit for human consumption, but exempt from the specific purity standard (Reg. 2.2.1(16)) that applies to refined oils of that type.
- **Solvent-extracted oil:** any vegetable oil obtained from oil-bearing material via solvent extraction (as opposed to mechanical pressing).
- **Vegetable oils (general):** oils produced from oilcakes, oilseeds, or other oil-bearing plant material, containing glycerides.
- **Vegetable oil product:** the result of subjecting one or more edible oils to refining, blending, hydrogenation, interesterification, and/or winterization (fractioning oils/fats through cooling).
- **Margarine:** an emulsion of edible oils and fats with water.

**Relevance:** Indian packaged snacks frequently list "refined palm oil," "vegetable oil," or (less commonly now) "hydrogenated vegetable oil" as an ingredient — this is the precise regulatory grounding for explaining what those terms mean and how raw/refined/hydrogenated differ. Directly relevant to Lay's ("edible vegetable oil," batch-dependent palmolein/rice bran oil), Kurkure (rice bran oil), McVitie's (edible vegetable oil, palm oil), and others in `products_compiled.json`.

**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Chapter 1 (amended consolidation, amendment markers to at least "77," consolidation date not stated in source).
**Last verified:** date not stated in source — amendment markers present to at least "77"
**Metadata:** `{doc_type: "regulatory", entity: "vegetable_oil_processing_terms", regulation: "FSS_Additives_2011_ch1_amended", source: "FSSAI", superseded_by: null}`

---

## Chunk 29
**Topic:** Irradiation-Related Definitions

**Status:** Same source as Chunk 28 (amended Chapter 1). Content covers irradiation-process definitions relevant to food processing terminology — not yet needed for grounding against any of the 23 current catalog products (none use irradiation on their label), so full text wasn't prioritized for extraction into this reassembly pass. Revisit if a future product addition involves irradiated ingredients (e.g. certain spices).
**Source:** FSSAI, Food Products Standards and Food Additives Regulations, 2011, Chapter 1 (amended consolidation).
**Metadata:** `{doc_type: "regulatory", entity: "irradiation_definitions", regulation: "FSS_Additives_2011_ch1_amended", source: "FSSAI"}`

---

## Chunk 30
**Topic:** Trans Fat — FSSAI Regulatory Limit (Vegetable Oils & Fats)

**Regulation:** Refined vegetable oil, interesterified fat, vanaspati, bakery/industrial margarine, and vegetable/mixed fat spreads must not exceed **2% trans fatty acids by weight** (phased down from 5% pre-2021, to 3% from 1 Jan 2021, to 2% from 1 Jan 2022).

**Relevance:** Hard regulatory ceiling — distinct from WHO's health-based recommendation (`nutrition_knowledge_base.md` Chunk 4b) that trans fat intake stay under 1% of total daily *energy*. A product can be fully FSSAI-compliant (≤2% trans fat by weight in the oil) while still contributing meaningfully to WHO's stricter energy-based limit — the two are measured differently and aren't directly interchangeable.

**Source:** FSSAI Food Product Standards, Ch. 2.2.6(1)(vii)(b), 2.2.3, 2.2.5.
**Last verified:** 2025-08-01 (document version date)
**Metadata:** `{doc_type: "regulatory", entity: "trans_fat", regulator: "FSSAI", source: "FSSAI Ch 2.2"}`

---

## Chunk 31
**Topic:** Vanaspati (Hydrogenated Vegetable Oil) — Definition & Key Requirements

**Definition:** Vanaspati is any refined edible vegetable oil (or blend) that has undergone hydrogenation or chemical/enzymatic interesterification, typically made from groundnut, cottonseed, or sesame oil (or FSSAI-approved substitutes).

**Key regulatory requirements:** Must contain a minimum level of raw/refined sesame (til) oil sufficient to pass the Baudouin colour test; must not exceed 2% trans fat by weight; must be fortified with synthetic Vitamin A (minimum 25 IU/gram at packing); residual nickel (from the hydrogenation catalyst) capped at 1.5 ppm; no colour resembling ghee is permitted.

**Relevance:** Directly applicable when "vanaspati" appears in a product's ingredient list. None of the current 23 catalog products list it — flag if a future addition does.

**Source:** FSSAI Food Product Standards, Ch. 2.2.6(1).
**Last verified:** 2025-08-01
**Metadata:** `{doc_type: "regulatory", entity: "vanaspati", regulator: "FSSAI", source: "FSSAI Ch 2.2"}`

---

## Chunk 32
**Topic:** Refined Vegetable Oil — Regulatory Definition

**Definition:** Oil obtained from vegetable-oil-bearing material via expression or solvent extraction, then deacidified (alkali or physical refining), degummed, bleached, and steam-deodourised. No chemical agent beyond the permitted refining process may be used. The specific base oil must be named on the label — "refined vegetable oil" alone is a defined category, but the source oil must still be disclosed.

**Key limits:** Moisture ≤0.10%; trans fat ≤2% by weight (post-2022); acid value ≤0.6.

**Relevance:** "Refined vegetable oil" or "refined [X] oil" is one of the most common ingredient-list entries in packaged snacks — directly relevant to Lay's, McVitie's, Britannia products. Complements Chunk 28 (general processing terminology) with the specific numeric standard for the refined-oil category.

**Source:** FSSAI Food Product Standards, Ch. 2.2.1(16).
**Last verified:** 2025-08-01
**Metadata:** `{doc_type: "regulatory", entity: "refined_vegetable_oil", regulator: "FSSAI", source: "FSSAI Ch 2.2"}`

---

## Chunk 33
**Topic:** Margarine / Vegetable Fat Spread — Vitamin A Fortification Requirement

**Regulation:** Table margarine and vegetable fat spreads must contain not less than 25–30 IU of synthetic Vitamin A per gram at the time of packing/sale, verified by a positive Antimony Trichloride (Carr-Price) test.

**Relevance:** Notable for any product-comparison query about margarine/spread vs. butter/ghee — margarine is mandatorily fortified with Vitamin A by regulation, unlike ghee or butter.

**Source:** FSSAI Food Product Standards, Ch. 2.2.5(1), 2.2.5(3).
**Last verified:** 2025-08-01
**Metadata:** `{doc_type: "regulatory", entity: "margarine_fortification", regulator: "FSSAI", source: "FSSAI Ch 2.2"}`

---

## Chunk 34
**Topic:** Food Additive — Definition and Justification for Use

**Definition:** A food additive is any substance not normally consumed as a food by itself and not normally used as a typical food ingredient, intentionally added to food for a technological (including organoleptic) purpose during manufacture, processing, preparation, treatment, packing, or transport, which becomes (or may reasonably be expected to become) a component of the food or affects its characteristics. Contaminants and substances added purely to maintain/improve nutritional quality are excluded from this definition.

**Justification requirement:** Use of a food additive is only justified where it (a) preserves nutritional quality, (b) serves special dietary needs, (c) improves keeping quality or organoleptic properties without deceiving the consumer, or (d) aids manufacture/processing — and only where these objectives cannot be achieved by other economically/technologically practicable means. An additive cannot disguise faulty raw materials or poor manufacturing practice.

**Source:** FSSAI, Food Safety and Standards (Food Products Standards and Food Additives) Regulations, Chapter 3, Section 3.1.1(4) & (7), Version 4.
**Last verified:** 2025-08-01
**Metadata:** `{doc_type: "regulatory", entity: "food_additive_general", jurisdiction: "FSSAI_india", source: "FSSAI Chapter 3", last_verified: "2025-08-01"}`

---

## Chunk 35
**Topic:** Acceptable Daily Intake (ADI) and Good Manufacturing Practice (GMP) for Additives

**Guidance:** ADI is the amount of an additive, expressed on a body-weight basis, that can be ingested daily over a lifetime without appreciable health risk. Additives meeting ADI criteria must still be used within GMP bounds: (a) quantity limited to the lowest level necessary for the intended effect; (b) any portion not intended to have a technical effect is reduced as far as reasonably possible; (c) food-grade quality, handled like any other food ingredient.

**Relevance:** The general regulatory backbone for any "is this additive safe" question — permitted-additive status is conditional on dose (ADI) and manufacturing discipline (GMP), not an unconditional green light.

**Source:** FSSAI, Chapter 3, Section 3.1.1(5), (6), (8), Version 4.
**Last verified:** 2025-08-01
**Metadata:** `{doc_type: "regulatory", entity: "food_additive_general", jurisdiction: "FSSAI_india", source: "FSSAI Chapter 3", last_verified: "2025-08-01"}`

---

## Chunk 36
**Topic:** Carry-Over of Food Additives — When It's Permitted (Chapter 3 detail)

**Guidance:** An additive may legitimately appear in a finished food without direct addition, via carry-over from a raw material or ingredient, provided: the additive was permitted in that raw material to begin with; its level didn't exceed the max use level there; and the carried-over amount in the final food doesn't exceed what normal manufacturing practice would introduce. **Carry-over is explicitly NOT permitted** for infant formula, follow-up formula, formula for special medical purposes for infants, or complementary foods for infants and young children.

**Relevance:** Explains why an additive might appear on an ingredient panel without being separately declared as "added." Complements the general carry-over principle (Chunk 12) with the infant-formula zero-tolerance carve-out.

**Source:** FSSAI, Chapter 3, Section 3.1.1(10), Version 4.
**Last verified:** 2025-08-01
**Metadata:** `{doc_type: "regulatory", entity: "food_additive_general", jurisdiction: "FSSAI_india", source: "FSSAI Chapter 3", last_verified: "2025-08-01"}`

---

## Chunk 37
**Note:** Merged from two source chunks — REG-C3-4 and session1's R2, which were near-duplicates of the same underlying table; product callouts and the Prop 65/colour-160c notes from R2 folded in here, R2 dropped rather than kept as a separate near-identical chunk.
**Topic:** Caramel Colour (INS 150) — Four Types and 4-MEI Limits

**Classification:** Caramel colour is prepared from food-grade carbohydrates and comes in four regulatory types based on processing agents used:
- **Type I (Plain, 150a):** heated carbohydrates only, no ammonium or sulphite compounds.
- **Type II (Caustic sulphite, 150b):** sulphite compounds used, no ammonium.
- **Type III (Ammonia process, 150c):** ammonium compounds used, no sulphite.
- **Type IV (Ammonia sulphite, 150d):** both ammonium and sulphite compounds used.

**4-Methylimidazole (4-MEI) limits:** Only the ammonia-process types carry a specified 4-MEI ceiling — Type III (150c) capped at 300 mg/kg (or 200 mg/kg on equivalent colour basis); Type IV (150d) capped at 1000 mg/kg (or 250 mg/kg on equivalent colour basis). Types I and II (150a/150b) have **no** specified 4-MEI limit, since 4-MEI is a byproduct specifically of the ammonia-process reaction.

**Why it matters:** 4-MEI has drawn international regulatory scrutiny (notably California Prop 65 listing) as a possible carcinogen based on animal studies, though FSSAI's framework treats it as a controlled-limit byproduct rather than a prohibited substance — permitted use within these ceilings, not an outright ban.

**Relevance to product set:** Sunfeast Dark Fantasy Choco Fills declares both 150c and 150d; Bournvita declares 150c; Coca-Cola and Diet Coke both declare 150d; Kellogg's Multigrain Chocos declares 150a and 150d; Britannia Brown Bread declares 150a (plain — not subject to 4-MEI limits at all). Directly resolves the project's flagged "150c/150d 4-MEI regulatory history" candidate. No label states which specific type is used at what concentration — the label just cites the INS number, not the batch's actual 4-MEI content.

**Additional flag:** Colour 160c (paprika extract, from Kurkure) is a materially different additive family — carotenoid-based, not caramel — and needs its own separate verification pass; not resolved by this chunk.

**Source:** FSSAI, Chapter 3, Section 3.2.1, Item 7 (Caramel), Table 1/2, Version 4.
**Last verified:** 2025-08-01 / 2026-08-12 (two source sessions independently confirmed the same figures)
**Metadata:** `{doc_type: "regulatory", entity: "colour_150_caramel", jurisdiction: "FSSAI_india", source: "FSSAI Chapter 3", limit_verified: true, last_verified: "2025-08-01"}`

---

## Chunk 38
**Topic:** Sweeteners — Caloric vs. Non-Caloric Classification

**Classification:** FSSAI classifies sweetener food additives into two groups by caloric contribution relative to sucrose per equivalent unit of sweetening capacity:
- **Caloric sweeteners** (>2% of sucrose's caloric value per equivalent sweetness): sorbitol, sorbitol syrup, mannitol, isomalt, polyglycitol syrup, maltitol, maltitol syrup, lactitol, xylitol.
- **Non-caloric sweeteners** (<2%): erythritol, steviol glycosides, thaumatin, aspartame, sucralose, neotame, acesulfame potassium, aspartame-acesulfame potassium salt, saccharins.

**Relevance:** Diet Coke declares sweeteners 951 (aspartame) and 950 (acesulfame potassium) — both non-caloric per this classification. Cross-references directly with the WHO non-sugar-sweetener guidance (`nutrition_knowledge_base.md` Chunk 8).

**Source:** FSSAI, Chapter 3, Section 3.2.2, Version 4.
**Last verified:** 2025-08-01
**Metadata:** `{doc_type: "regulatory", entity: "sweetener_general", jurisdiction: "FSSAI_india", source: "FSSAI Chapter 3", last_verified: "2025-08-01"}`

---

## Chunk 39
**Topic:** Flavouring Substances — Natural / Nature-Identical / Artificial Definitions

**Definitions:**
- **Natural flavours:** obtained exclusively by physical processes from vegetable/animal raw materials.
- **Nature-identical flavouring substances:** chemically isolated from aromatic raw materials, or synthetic — but chemically identical to substances that occur naturally in food.
- **Artificial flavouring substances:** substances not identified in any natural food product, processed or not.

**Relevance:** Appears on nearly every one of the 23 collected products' ingredient panels (e.g. "Nature Identical & Artificial Flavouring Substances (Vanilla)" on Parle-G; "Natural Flavours and Natural Flavouring Substances" on Haldiram's and Yippee). High-frequency retrieval target — "artificial" here specifically means "not found in nature," not "synthetically made" (nature-identical substances are also often synthetic). Consumer-facing companion to this is the elevated Tier-1.5 entry in `ingredient_kb_tier2.md`.

**Source:** FSSAI, Chapter 3, Section 3.3.1(1), Version 4.
**Last verified:** 2025-08-01
**Metadata:** `{doc_type: "regulatory", entity: "flavouring_substance_general", jurisdiction: "FSSAI_india", source: "FSSAI Chapter 3", last_verified: "2025-08-01"}`

---

## Chunk 40
**Topic:** Anticaking Agent in Flavours — INS 551 Maximum Level

**Guidance:** Synthetic amorphous silicon dioxide (INS 551) may be used as an anticaking agent in powder flavouring substances up to a maximum of **2% by weight.**

**Relevance:** Yippee Magic Masala Noodles declares Anticaking Agent (INS 551) in its masala seasoning — this is the specific regulatory basis and ceiling.

**Source:** FSSAI, Chapter 3, Section 3.3.1(3), Version 4.
**Last verified:** 2025-08-01
**Metadata:** `{doc_type: "regulatory", entity: "additive_551_silicon_dioxide", jurisdiction: "FSSAI_india", source: "FSSAI Chapter 3", last_verified: "2025-08-01"}`

---

## Chunk 41
**Topic:** Sodium Metabisulphite (INS 223) — Identity Note and Scope Limitation

**Identity:** Sodium metabisulphite is a sulphite-class food additive (colourless crystals or white-to-yellowish crystalline powder, characteristic sulphur-dioxide odour), regulated as a preservative-category substance.

**Scope limitation:** This source only specifies identity and manufacturing purity criteria (e.g. minimum 95% purity as Na2S2O5). It does **NOT** state permitted use levels by food category, and is **not** the source for sulphite allergen-labelling requirements (that's Chunk 14). Do not generate a claim from this chunk alone about whether 223 is "permitted" in a specific product category or at what level.

**Relevance:** McVitie's Digestive declares Dough Conditioner (INS 223) — resolves identity but not permitted-use-level or allergen-declaration questions.

**Source:** FSSAI, Chapter 3, Section 3.2.7, Version 4.
**Last verified:** 2025-08-01
**Metadata:** `{doc_type: "regulatory", entity: "additive_223_sodium_metabisulphite", jurisdiction: "FSSAI_india", source: "FSSAI Chapter 3", last_verified: "2025-08-01", scope_limitation: "identity_only_not_permitted_levels"}`

---

## Chunk 42
**Topic:** Sodium Benzoate (INS 211) — Identity, Purity, and Category-Specific Limit

**Identity/purity (verified):** Chemical identity C7H5O2Na, CAS 532-32-1. Minimum 99.0% purity, arsenic ≤3mg/kg, lead ≤2mg/kg.

**Category-specific maximum use level:** **✅ RESOLVED 2026-08-18.** FSSAI Appendix A, Table 10 ("List of food additives for use in Food products"), Section I (Preservatives), entry 1 — "Benzoic Acid & its Sodium & Potassium Salt or both (Calculated as Benzoic Acid)" — lists **Tomato Ketchup: 750 ppm maximum**, matching the secondary-source figure this entry previously couldn't confirm. The same table entry also covers **Culinary Paste/Other Sauces: 750 ppm maximum** and **Soyabean Sauce: 750 ppm maximum** (same 16-column food-products table that resolved DATEM/472e and several other entries this session — see `ingredient_knowledge_base.md`'s INS 472e entry and `PHASE3_TESTING_LOG.md` Finding 13 for the document itself). Read directly from extracted primary-source PDF text (FSSAI's original 2011 Appendix A, via a state-government mirror + local `pypdf` extraction), not a secondary summary. Note the regulatory convention: the limit is expressed "calculated as Benzoic Acid," not as sodium benzoate salt weight — a real technical nuance worth preserving if this figure is ever quoted precisely.

**Function:** Preservative — inhibits bacterial, yeast, and mould growth in acidic foods.

**Health consideration:** Under specific conditions, sodium benzoate can react with ascorbic acid (vitamin C) to form trace benzene, a recognized carcinogen. Most relevant to beverages combining both additives.

**Relevance:** Kissan Fresh Tomato Ketchup (declares E211), Maggi Hot & Sweet Chilli Tomato Sauce (declares Preservative 211) — both now have a confirmed 750 ppm ceiling.

**Source:** FSSAI, Chapter 3.2.9(1) (identity/purity); FSSAI Food Products Standards and Food Additives Regulations, 2011, Part II, Appendix A, Table 10 (category limit, confirmed 2026-08-18).
**Last verified:** 2026-08-18 (category limit now confirmed against primary source; identity/purity was already confirmed 2026-08-12)
**Metadata:** `{doc_type: "regulatory", entity: "sodium_benzoate_INS211", source: "FSSAI Appendix A Table 10, confirmed 2026-08-18: Tomato Ketchup/Culinary Paste/Soyabean Sauce all 750ppm max as benzoic acid", limit_verified: true, last_verified: "2026-08-18"}`

---

## Chunk 43
**Note:** ⚠️ PROVISIONAL — secondary source.
**Topic:** Carbonated & Caffeinated Beverages — Caffeine Limits (FSSAI Ch. 2.10)

**Regulation:** Ordinary carbonated water/soft drinks are capped at 200 ppm (mg/litre) caffeine under the base standard. A separate "Caffeinated Beverage" sub-category (reg. 2.10.6(2)) applies above 145 mg/L, with a 300 mg/L ceiling, requiring stated max-caffeine-per-serve, a "not recommended for children/pregnant women/caffeine-sensitive persons" warning, and a "not more than 500 ml per day" caution.

**Relevance:** Coca-Cola (87 mg/L) and Diet Coke (100 mg/L) both sit comfortably under both thresholds.

**Source:** Multiple secondary sources citing FSSAI Regulations 2011, sub-regulation 2.10.6 and 2016/2017 amendments. **NOT verified against primary gazette text.**
**Last verified:** 2026-08-13 (secondary sources only)
**Metadata:** `{doc_type: "regulatory", entity: "caffeine_limit", regulator: "FSSAI", source: "secondary — needs primary verification"}`

---

## Chunk 44
**Note:** ⚠️ PROVISIONAL — secondary source.
**Topic:** Curd / Dahi — Compositional Standard (FSSAI Ch. 2.1)

**Regulation:** Plain dahi/curd must carry the same minimum milk fat and SNF percentage as the milk it was made from. Commonly cited benchmarks: full-cream curd ≥3.0% fat, toned-milk curd ≥0.5% fat, SNF ≥8.5% both, titratable acidity 0.5–1.0% (as lactic acid), minimum live lactic-acid-bacteria count. Curd not made from boiled/pasteurised/sterilised milk cannot legally be sold.

**Relevance:** Amul Masti Curd — explains why declared fat content varies by "toned" vs. "full cream."

**Source:** Multiple secondary sources citing FSSAI Regulations, Chapter 2.1, as revised 2017. **NOT verified against primary gazette text.**
**Last verified:** 2026-08-13 (secondary sources only)
**Metadata:** `{doc_type: "regulatory", entity: "curd_dahi_standard", regulator: "FSSAI", source: "secondary — needs primary verification"}`

---

## Chunk 45
**Note:** ⚠️ Mixed status — sodium-benzoate figure confirmed, fortification/health-drink claims cross-corroborated, compositional standard still provisional (see 2026-08-18 updates below); contains Chunks formerly B15/B16/B17 combined by topic proximity.
**Topic:** Tomato Ketchup Standard, Fortification Framework, and "Health Drink" Labelling Advisory

**Ketchup/sauce standard (Ch. 2.3):** Product made by blending tomato juice/purée/paste with sweeteners, salt, vinegar, spices, condiments, then heated to consistency. Must contain ≥25.0% total soluble solids (salt-free basis) and ≥1.0% acidity (as acetic acid). **The 750 ppm sodium-benzoate figure (as Chunk 42) is now confirmed** against FSSAI Appendix A Table 10 (2026-08-18, see Chunk 42) — this part of the chunk is no longer provisional. **The compositional standard itself (25% TSS, 1% acidity) is still unverified** against primary source; Appendix A only covers additive limits, not compositional standards, so this session's resolution doesn't extend to that part. Relevant to Kissan Ketchup, Maggi Hot & Sweet Sauce.

**Fortification framework (2018 Regs):** Fortification is **voluntary**, not mandatory, unless a category standard separately requires it. **2026-08-18 update:** the voluntary/optional nature and the "+F" logo requirement are corroborated by multiple independent sources — Food Safety and Standards (Fortification of Foods) Regulations, 2018, notified 2018-08-02, FBO compliance deadline 2019-01-01, +F logo required per Schedule II wherever fortification is claimed. **The specific claim that breakfast cereals and bakery wares are named-eligible categories requiring non-heme iron sources is still not independently confirmed** — this detail wasn't corroborated by the sources checked this session, still resting on the original secondary source alone. Relevant to Kellogg's Corn Flakes, Kellogg's Chocos, Britannia Brown Bread, Bournvita — all four are voluntarily fortified, not compelled to be.

**"Health drink" labelling (2024 clarification):** Malted beverage mixes like Bournvita do not meet the definition of "health drink"/"energy drink" under FSSAI's Food Category System. **2026-08-18 update — corroborated with exact dates and legal basis, still an advisory not a codified standard:** FSSAI issued the advisory to e-commerce food business operators on 2024-03-28; the Ministry of Commerce and Industry directed e-commerce platforms to remove Bournvita and similar products from the "health drinks" category on 2024-04-10. FSSAI's own stated legal basis: the term "Health Drink" is not defined or standardized anywhere under the Food Safety and Standards Act and regulations — "malt-based beverage," "dairy-based beverage," or "cereal-based beverage" are the correct FSSAI category terms. Confirmed via multiple independent news/compliance sources reporting consistent dates and wording. **This is still a labelling/marketing advisory, not a compositional standard** — no chapter/section citation exists for it, unlike every other chunk in this file, and that's a structural fact about the advisory itself, not a gap in this KB's research. **Unresolved design question, unchanged by this update:** this doesn't fit the typed-claim system ([FACT]/[REGULATORY]/[INTERPRETATION]/[UNCERTAIN]) cleanly — it's a real regulatory action but an advisory, not codified law. Decide whether it needs a new claim type or [REGULATORY]-with-caveat treatment before Phase 6.

**Source:** Multiple secondary sources (compliance blogs, news coverage), cross-corroborated 2026-08-18 for the fortification-voluntary and health-drink-labelling claims specifically (dates and legal-basis wording consistent across independent sources). **The compositional standard (25% TSS, 1% acidity) and the specific breakfast-cereal/non-heme-iron fortification detail remain NOT verified against primary gazette text or primary source PDFs.**
**Last verified:** 2026-08-18 (sodium-benzoate figure and health-drink/fortification-voluntary claims corroborated; compositional standard and non-heme-iron detail still secondary-only)
**Metadata:** `{doc_type: "regulatory", entity: "tomato_ketchup_sauce_standard,fortification_framework,health_drink_labelling", regulator: "FSSAI/Commerce Ministry", source: "sodium-benzoate figure confirmed via Appendix A 2026-08-18; fortification-voluntary and health-drink-labelling claims cross-corroborated 2026-08-18; compositional standard and non-heme-iron detail still secondary-only", claim_type_note: "health_drink portion is advisory, not codified regulation"}`

---

## Chunk 46
**Note:** Recovered this pass — drafted during the original sequencing-pushback session on Chapter 2.7, never merged into the trunk.
**Topic:** Artificial Sweetener — Labeling Declaration Requirement (Confectionery)

**Regulation:** Where an artificial sweetener has been added to a confectionery product (sugar boiled confectionery, lozenges, or chewing/bubble gum) under Regulation 3.1.2/3.1.3, this must be declared on the label as specified in Regulation 2.4.5 (clauses 24, 25, 26, 28 & 29) of the Food Safety and Standards (Packaging and Labelling) Regulations, 2011.

**Applies to:** Any product using non-sugar/artificial sweeteners as a full or partial sugar substitute — relevant for "sugar-free," "no added sugar," or "diet" product label claims.

**Note:** For lozenges specifically, if only permitted artificial sweetener is used as the sweetening agent, the standard's minimum sucrose-content requirement (85% by weight) does not apply to that product.

**Source:** FSSAI Food Product Standards, Chapter 2.7 (Sweets & Confectionery), clauses 2.7.1–2.7.3, Version 1, 01.09.2023.
**Last verified:** 2023-09-01 (document version date)
**Metadata:** `{doc_type: "regulatory", entity: "artificial_sweetener", topic: "labeling_confectionery", source: "FSSAI Ch 2.7"}`

---

## Chunk 47
**Topic:** Isomaltulose as Sugar Substitute — Permitted Level

**Regulation:** Isomaltulose may be used at up to 50% (maximum) of total sugars in a product, provided this does not adversely affect product stability. This allowance appears consistently across sugar boiled confectionery, lozenges, chewing/bubble gum, chocolate, and ice lollies/edible ices standards.

**Applies to:** Any confectionery, chocolate, or frozen-dessert product claiming reduced sugar impact via isomaltulose substitution — a lower-glycemic-index sugar alternative rather than a non-nutritive sweetener.

**Distinction from Chunk 46:** Isomaltulose is a caloric sugar substitute (not an artificial/non-nutritive sweetener), so it does not trigger the same labeling declaration requirement as artificial sweeteners, though general ingredient labeling rules still apply.

**Relevance to current product set:** None of the 23 catalog products currently declare isomaltulose — retained for completeness and in case of future additions.

**Source:** FSSAI Food Product Standards, Chapter 2.7 (Sweets & Confectionery), clauses 2.7.1, 2.7.2, 2.7.3, 2.7.4, 2.7.5, Version 1, 01.09.2023.
**Last verified:** 2023-09-01 (document version date)
**Metadata:** `{doc_type: "regulatory", entity: "isomaltulose", topic: "sugar_substitution", source: "FSSAI Ch 2.7"}`

---

## Chunk 48
**Note:** Closes a real, previously-unflagged coverage gap — directly resolves Cadbury Dairy Milk's declared composition.
**Topic:** Chocolate — Compositional Minimums by Type

**Regulation:** FSSAI defines six chocolate types with distinct minimum-composition requirements (on a dry-basis, per cent by weight):

| Type | Total Fat (min) | Milk Fat (min) | Cocoa Solids (min) | Milk Solids (min) |
|---|---|---|---|---|
| Milk Chocolate | 25% | 2% | 2.5% | 10.5% |
| Plain Chocolate | 25% | — | 12% | — |
| White Chocolate | 25% | 2% | — | 10.5% |
| Blended Chocolate | 25% | — | 3.0% | 1–9% (range) |

Dark chocolate (a sub-type of plain chocolate) additionally requires ≥35% total cocoa solids on a dry-matter basis, of which ≥18% must be cocoa butter and ≥14% fat-free cocoa solids.

Vegetable fat other than cocoa butter is capped at 5% of the finished product (after deducting other added edible foodstuffs) without reducing minimum cocoa-material content.

**Relevance to current product set:** Cadbury Dairy Milk (milk chocolate) and Amul Dark Chocolate both fall under this standard — this is the compositional identity standard behind "milk chocolate" and "dark chocolate" as legal categories, not just marketing terms.

**Source:** FSSAI Food Product Standards, Chapter 2.7 (Sweets & Confectionery), clause 2.7.4, Version 1, 01.09.2023.
**Last verified:** 2023-09-01 (document version date)
**Metadata:** `{doc_type: "regulatory", entity: "chocolate_composition_standards", topic: "composition_standards", source: "FSSAI Ch 2.7"}`

---

## Chunk 49
**Note:** Closes a real, previously-unflagged coverage gap — directly resolves Cadbury Dairy Milk's exact label wording.
**Topic:** Cocoa Butter Equivalent — Mandatory Label Declaration

**Regulation:** If a chocolate product contains vegetable fats other than cocoa butter (used as a cocoa butter equivalent, per the standards in clause 2.7.4 §5(b)), the label must carry the following declaration in bold: **"CONTAINS COCOA BUTTER EQUIVALENT / VEGETABLE FAT IN ADDITION TO COCOA BUTTER."**

**Relevance to current product set:** Cadbury Dairy Milk's actual label reads "Contains Cocoa Butter Equivalent in addition to Cocoa Butter" — this chunk is the direct regulatory source for that exact wording. This was previously covered only informally in `ingredient_kb_tier2.md`'s elevated-entry section; this chunk gives it a formal `regulatory` doc_type citation, which the ingredient-KB entry itself lacked.

**Source:** FSSAI Food Product Standards, Chapter 2.7 (Sweets & Confectionery), clause 2.7.4, Version 1, 01.09.2023.
**Last verified:** 2023-09-01 (document version date)
**Metadata:** `{doc_type: "regulatory", entity: "cocoa_butter_equivalent", topic: "labeling", source: "FSSAI Ch 2.7"}`

---

## Chunk 50 — Non-Sugar Sweetener Limits in Carbonated Beverages
**Topic:** Non-Sugar Sweetener Limits — Carbonated Beverages (Category-Specific)

**Regulation:** In carbonated beverages specifically, non-sugar sweeteners are capped at: saccharin 100 ppm, acesulfame potassium 300 ppm, aspartame 700 ppm, sucralose 300 ppm, neotame 33 ppm.

**Relevance to current product set:** Diet Coke declares both 951 (aspartame) and 950 (acesulfame potassium). These category-specific ppm figures are more precise than the general sweetener table in Chunk 5 (which lists cross-category examples like biscuits/breads/carbonated water generically) — this is the correct lookup specifically for a carbonated beverage product.

**✅ CONFLICT RESOLVED 2026-08-18** (flagged during Phase 3 pipeline testing, 2026-08-13): `ingredient_knowledge_base.md`'s INS 951 entry previously stated 600 mg/kg, disagreeing with this chunk's 700 ppm figure. Investigated against independent secondary sources (not just re-asserting this chunk's own number): the 700 ppm figure here is confirmed as FSSAI's actual limit for the "carbonated water" category, consistently reported across multiple sources. The 600 mg/kg figure turned out to be real too, but misattributed — it's the EU's aspartame limit (600 mg/L under Regulation (EC) No. 1333/2008, ≈600mg/kg for a water-based beverage), not an FSSAI number, and had been mislabeled as FSSAI's in that entry's original drafting. `ingredient_knowledge_base.md` has been corrected to match this chunk's 700 ppm figure. This was a real jurisdiction mix-up between two genuine regulatory numbers, not a fabricated conflict — worth remembering as a concrete example of how KB conflicts can arise even when every individual number is independently real.

**Provenance note:** unlike Chunks 43–45, this was read directly from the primary FSSAI beverage-standards PDF text (quoted precisely during extraction), not a secondary source — but the chunk itself was never formally written up in the original session, which ended on a scoping question before drafting; it was recovered and formalized into this chunk in a later pass, since it's directly relevant to Diet Coke and more precise than Chunk 43's general caffeine coverage. Treating the extracted numbers as primary-source-confirmed, since the quoted figures came directly off the source PDF text at the time, not from web search — now independently corroborated by the 2026-08-18 resolution above.

**Source:** FSSAI Food Product Standards, beverage standards chapter (carbonated beverages, non-alcoholic).
**Last verified:** 2026-08-18 (700ppm figure independently corroborated against multiple secondary sources during conflict resolution; exact chapter/clause citation still not captured in the original extraction — flag for a follow-up primary-source page-number confirmation if court-level precision is ever needed)
**Metadata:** `{doc_type: "regulatory", entity: "sweetener_limits_carbonated_beverages", topic: "beverage_sweeteners", source: "FSSAI primary PDF + independently corroborated 2026-08-18, chapter/clause citation still incomplete"}`

---

## Reassembly note on chunk ordering
Chunks 28–29 sit before the fats/oils and Chapter 3 material despite covering general definitions rather than specific limits — this mirrors the original trunk's own ordering choice (content grouped by *source document*, not by conceptual hierarchy). `doc_type`/`entity` metadata, not chunk position, is what retrieval actually keys on — don't assume adjacent chunk numbers share a topic or a confidence level.

---

## Notes for Phase 5/6 (retrieval & grounding)

- **Chunking granularity:** each chunk is scoped to one additive class, one label-rule topic, or one claim-eligibility rule — matching the ingredient KB's planned granularity (one doc per ingredient).
- **`doc_type` is the load-bearing retrieval filter**, not file identity. Don't assume adjacent chunk numbers share a `doc_type` or a `last_verified` confidence level — Chunks 43–45 sit right next to fully-verified primary-source chunks but carry materially weaker provenance.
- **Known coverage gap:** additive/claim classes plausible for the 23-product catalog are covered; cross-check the actual unique-ingredient list against every `entity` value here to confirm nothing's missing.
- **INS 627/631/635 (Yippee, Maggi) has no chunk in this file** — see `ingredient_knowledge_base.md`'s own entry (rewritten 2026-08-18 after a stale pointer to this file was found broken). **The sodium-benzoate 750mg/kg figure (Chunk 42) is now confirmed** against FSSAI Appendix A Table 10, 2026-08-18 — can be stated as fact.
- **Version drift is a real failure mode, not hypothetical:** Chunks 14–17 are direct proof — the 2020-only labelling text would have produced a confidently wrong sweetener-warning answer. Chapter 3's colour standards (Chunk 37) also carry a dated drift warning: several synthetic colour provisions are being omitted effective 1 Feb 2026 — re-verify after that date.
- **Duplicate resolved, not just avoided:** Chunk 37 merges what were two independently-drafted near-identical chunks (REG-C3-4 and session1's R2) into one — a concrete example of a retrieval-quality bug caught before it shipped, worth mentioning in the eventual project writeup.
- **High-value downstream use case:** Chunks 18–22 (claim thresholds) let "can this product legally say 'low sugar'?" become a deterministic SQL+threshold check against the structured nutrition table, rather than a RAG question — route it as a product-fact/derived-calculation query (pipeline step 2), not through retrieval.
