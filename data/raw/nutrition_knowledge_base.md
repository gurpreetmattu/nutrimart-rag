# General Nutrition Knowledge Base — CORRECTED (this session found the Project's copy was stale)
**Source PDFs processed:** WHO "Guideline: Sugars intake for adults and children" (2015); WHO "Healthy diet" fact sheet (26 January 2026); WHO "REPLACE Trans Fat: Frequently Asked Questions" (WHO/NMH/NHD/18.7, May 2018); WHO "Guideline: Sodium intake for adults and children" (2012); WHO "Saturated fatty acid and trans-fatty acid intake for adults and children: WHO guideline summary" (2023)
**Status:** Phase 2 — general nutrition sub-base, 12 chunks. **Reconstruction note:** the copy previously in this Project stopped at Chunk 8 and never included Chunks 9–12, and Chunks 4a/4b were the pre-merge originals rather than the versions carrying WHO recommendation-strength and GRADE evidence-certainty data. Both gaps closed in this pass, verbatim from source sessions.
**Known remaining gap, not closed here:** a separate session drafted 4 Codex/WHO international nutrient-declaration chunks (`jurisdiction: "international_codex"` — NRV-NCD thresholds, nutrient content claim thresholds, FOPL context) into a *different* file (`regulatory_knowledge_base.md`, an earlier, now-superseded name), deliberately kept out of this file to avoid conflating Codex international guidance with FSSAI Indian law. Those were never recovered in this reconstruction session and aren't part of this file. Flag if you want them pulled next.
**Chunking policy (codified during the NSS expansion, applies retroactively to justify the 4a/4b split too):** Default to one chunk per topic. Split a topic into multiple chunks only when it has genuinely distinct query-facets that would otherwise dilute a single bloated chunk (e.g. eligibility/scope vs. quantitative evidence vs. comparative/practical application) — not just because a source PDF is long. Revisit if Phase 7 eval doesn't confirm finer granularity actually helps Recall@5.
**Open design gap for Phase 6, logged not resolved:** the typed-claim system has no rule for varying evidence confidence *within* WHO guidance — e.g. Chunk 4a's ≤10% SFA limit is a strong recommendation from moderate-certainty evidence, but its "reduce further" clause is conditional from very-low-certainty evidence; both would currently get the same claim type. Needs a confidence-tier rule before Phase 6.
**Query routing gap for Phase 5, logged not resolved:** metadata-scoped retrieval currently filters by "ingredients present in the product," but a comparative query like "should I pick the diet version" needs cross-entity retrieval that isn't ingredient-triggered at all. A `comparison_group: "sugar_vs_sweetener"` metadata tag was added to Chunk 8a linking `added_sugar` and `non_sugar_sweeteners` as a hook for this — currently inert, needs a TODO in the eventual ingestion script so it isn't silently dropped (same flag as the FSSAI KB's `comparison_group` note).

---

## Chunk 1
**Topic:** Added/Free Sugars — Recommended Daily Limit

**Guidance:** WHO recommends limiting free sugars intake to less than 10% of total daily energy intake, with a conditional recommendation to further reduce to below 5% for additional health benefits. For a person consuming ~2000 kcal/day, 10% equals about 50g (~12 level teaspoons) of free sugars.

**Applies to:** free sugars — monosaccharides and disaccharides added to foods and beverages by the manufacturer, cook or consumer, plus sugars naturally present in honey, syrups, fruit juices and fruit juice concentrates. Does NOT include intrinsic sugars in whole fruit/vegetables or lactose naturally in milk.

**Evidence basis:** Strong recommendation (10% threshold) based on moderate-quality evidence linking free sugars to body weight and dental caries. Conditional recommendation (5% threshold) based on very-low-quality ecological evidence on dental caries dose-response.

**Source:** WHO, "Guideline: Sugars intake for adults and children," 2015, pp.4-5, 16-17; reaffirmed in WHO "Healthy diet" fact sheet, 26 January 2026.
**Last verified:** 2026-01-26
**Metadata:** `{doc_type: "nutrition_general", entity: "added_sugar", source: "WHO", last_verified: "2026-01-26"}`

---

## Chunk 2
**Topic:** Sugar Intake and Body Weight — Evidence

**Finding:** Reducing free sugars intake is associated with reduced body weight in adults (moderate-quality evidence, RCTs); increasing free sugars intake is associated with a comparable weight increase. In children, evidence for weight gain from higher sugar-sweetened beverage intake is of low quality but directionally consistent (higher odds of overweight/obesity with highest sugar-sweetened beverage intake).

**Mechanism:** Free sugars increase overall energy density of diets and may promote positive energy balance; effect on weight results from excess energy intake, not a unique metabolic effect of sugar itself.

**Source:** WHO, "Guideline: Sugars intake for adults and children," 2015, p.3, Annex 1 (GRADE Tables 1-4).
**Last verified:** 2015 (original publication)
**Metadata:** `{doc_type: "nutrition_general", entity: "added_sugar", topic: "body_weight", source: "WHO"}`

---

## Chunk 3
**Topic:** Sugar Intake and Dental Caries — Evidence

**Finding:** Positive dose-response relationship between free sugars intake and dental caries, observed at intakes well below 10% of total energy — including below 5%. Higher dental caries rates occur when free sugars exceed 10% of total energy vs. below it; further reduction below 5% shows continued benefit in ecological studies (very-low-quality evidence, Japan population data).

**Note:** Dental caries effects are cumulative over the lifecourse; even small reductions in childhood sugar intake matter for adult dental health.

**Source:** WHO, "Guideline: Sugars intake for adults and children," 2015, p.3-4, Annex 1 (Tables 5-6).
**Last verified:** 2015 (original publication)
**Metadata:** `{doc_type: "nutrition_general", entity: "added_sugar", topic: "dental_caries", source: "WHO"}`

---

## Chunk 4a
**Note:** Merged/updated — carries recommendation-strength and GRADE evidence-certainty data not in the original.
**Topic:** Saturated Fat — Recommended Limit & Evidence Strength

**Guidance:** Adults and children should reduce saturated fatty acid (SFA) intake to ≤10% of total daily energy intake (**strong recommendation**; moderate-certainty evidence — reduces LDL cholesterol, reduces CVD risk). WHO further suggests reducing SFA below 10% for additional benefit (**conditional recommendation**; very-low-certainty evidence). Total fat should generally be ≤30% of total daily energy for adults (minimum 15%, since linoleic and α-linolenic acid are essential and diet-only).

**Replacement matters:** Health benefit depends on what replaces the SFA, not just cutting SFA in isolation.
- Replacing SFA with **polyunsaturated fat** → reduced CVD risk (strong evidence, moderate certainty)
- Replacing with **plant-based monounsaturated fat** or **fibre-rich carbohydrates** (whole grains, vegetables, fruits, pulses) → reduced risk (conditional, mainly observational evidence)
- Replacing with **refined carbohydrates or mixed/animal protein** → little or no benefit, possible increased risk

**Relevance:** Useful for product-comparison queries where a "low-fat" product substitutes SFA with refined starch or sugar — that substitution is not supported as a health improvement by this evidence.

**Sources of concern:** Fatty meat, butter, palm/coconut oil, cream, cheese, ghee, lard.

**Source:** WHO, "Healthy diet" fact sheet, 26 January 2026; WHO, "Saturated fatty acid and trans-fatty acid intake for adults and children: WHO guideline summary," 2023, pp.6-9.
**Last verified:** 2026-01-26 (fact sheet); 2023 (guideline)
**Metadata:** `{doc_type: "nutrition_general", entity: "saturated_fat", source: "WHO"}`

---

## Chunk 4b
**Note:** Merged/updated — carries recommendation-strength and GRADE evidence-certainty data not in the original.
**Topic:** Trans Fat — Recommended Limit & Evidence Strength

**Guidance:** Adults and children should reduce trans-fatty acid (TFA) intake to ≤1% of total daily energy intake (**strong recommendation**; moderate-certainty evidence — reduces LDL cholesterol, reduces risk of all-cause mortality, CVD, coronary heart disease). WHO further suggests going below 1% for additional benefit (**conditional recommendation**; low-certainty evidence).

**Industrial vs. ruminant TFA:** The evidence did not support treating industrially-produced TFA (from partial hydrogenation — baked/fried goods, packaged snacks, some cooking oils) differently from ruminant TFA (naturally occurring in meat/dairy from cattle, sheep, goats) at equivalent intake levels. A product label listing "trans fat" does not need this sub-distinction to be evaluated against the limit.

**Preferred replacement:** Polyunsaturated or monounsaturated fat from plant sources (conditional recommendation). Replacing TFA with saturated fat showed no improvement in outcomes — SFA is not a preferred substitute for TFA.

**Sources of concern:** Baked/fried foods, pre-packaged snacks (frozen pizza, pies, cookies, biscuits, wafers), some cooking oils/spreads (industrial trans fat); meat and dairy from ruminant animals (ruminant trans fat).

**Note:** Industrially-produced trans fats should be avoided entirely, not just limited, per WHO policy guidance (REPLACE initiative).

**Source:** WHO, "Healthy diet" fact sheet, 26 January 2026; WHO, "Saturated fatty acid and trans-fatty acid intake for adults and children: WHO guideline summary," 2023, pp.6-8, 10-11.
**Last verified:** 2026-01-26 (fact sheet); 2023 (guideline)
**Metadata:** `{doc_type: "nutrition_general", entity: "trans_fat", source: "WHO"}`

---

## Chunk 5
**Note:** Updated — carries recommendation-strength grading and an exclusions clause not in the original.
**Topic:** Sodium/Salt — Recommended Daily Limit

**Guidance:** Adults should limit salt intake to less than 5g/day (equivalent to 2g/day sodium). Children's limits are lower, scaled to energy intake. WHO's full sodium guideline (2012) grades this a **strong recommendation** for adults (≥16 years) — desirable effects on blood pressure and CVD/stroke/CHD risk are judged to clearly outweigh undesirable effects, so it can be applied as policy in most settings. For children (2-15 years), reduction is also a strong recommendation, scoped to blood pressure *control* (preventing an age-related rise) rather than direct CVD outcome evidence.

**Common sources:** Processed foods (ready meals, processed meats like bacon/ham/salami, cheese, salty snacks), bread, and salt added during cooking (bouillon, stock cubes, soy sauce, fish sauce) or at the table.

**Related nutrient:** Potassium intake of at least 90 mmol/day (3510 mg/day) for adults can help mitigate sodium's blood-pressure effects; increased via fresh fruit and vegetables.

**Exclusions:** The recommendation does NOT apply to individuals with illnesses/drug therapy that risk hyponatraemia or require physician-supervised sodium intake (e.g. heart failure, type I diabetes) — those subpopulations were excluded from the evidence review.

**Source:** WHO, "Healthy diet" fact sheet, 26 January 2026; WHO, "Guideline: Sodium intake for adults and children," 2012, pp.2-3, 18.
**Last verified:** 2026-01-26
**Metadata:** `{doc_type: "nutrition_general", entity: "sodium", source: "WHO"}`

---

## Chunk 6
**Topic:** Carbohydrates and Dietary Fibre — General Guidance

**Guidance:** Carbohydrates should represent ~45-75% of total daily energy, primarily from whole grains, vegetables, fruits, and pulses rather than refined sources. Adults (>10 years) should aim for at least 25g/day of naturally-occurring dietary fibre (lower for younger children: 15g for ages 2-5, 21g for ages 6-9).

**Fruit/vegetable target:** At least 400g/day for people over 10 years old (250g for ages 2-5, 350g for ages 6-9).

**Note on fruit juice:** Even 100% fruit juice without added sugar contributes significant free sugars and should be limited.

**Source:** WHO, "Healthy diet" fact sheet, 26 January 2026.
**Last verified:** 2026-01-26
**Metadata:** `{doc_type: "nutrition_general", entity: "carbohydrate", source: "WHO"}`

---

## Chunk 7
**Topic:** Protein — Recommended Daily Intake

**Guidance:** Protein at 10-15% of total daily energy is generally sufficient for adults (~50-75g/day at 2000 kcal). Higher proportions may be appropriate for adolescents or those building muscle mass; excess protein places metabolic burden on the kidneys.

**Source:** WHO, "Healthy diet" fact sheet, 26 January 2026.
**Last verified:** 2026-01-26
**Metadata:** `{doc_type: "nutrition_general", entity: "protein", source: "WHO"}`

---

## Chunk 8a
**Note:** Replaces a stub Chunk 8 that only cited a one-line fact-sheet mention — this is the actual 2023 NSS guideline evidence base.
**Topic:** Non-Sugar Sweeteners — WHO Recommendation & Scope

**Guidance:** WHO suggests that non-sugar sweeteners (NSS) not be used as a means of achieving weight control or reducing the risk of noncommunicable diseases (NCDs). This is a **conditional** recommendation, not a strong one — meaning WHO is less certain the desirable effects outweigh the undesirable ones, and substantive policy discussion is expected before adoption, unlike a strong recommendation which can be adopted as policy in most situations.

**Definition of NSS:** All synthetic and naturally occurring/modified non-nutritive sweeteners not classified as sugars — includes acesulfame K, aspartame, advantame, cyclamates, neotame, saccharin, sucralose, stevia and stevia derivatives. Sugar alcohols (polyols) and low-calorie sugars are NOT classified as NSS under this guideline and the recommendation does not apply to them.

**Applies to:** General population of children and adults, including pregnant and lactating women.

**Does NOT apply to:** Individuals with pre-existing diabetes (disease management was out of scope for this guideline — evidence reviewed excluded diabetic-only populations). Also does not apply to NSS present in medications or personal care/hygiene products (e.g. toothpaste).

**Source:** WHO, "Use of non-sugar sweeteners: WHO guideline," Geneva, 2023, pp. vii-viii, 20, 23.
**Last verified:** 2023 (original publication; this is the primary evidence source — do not confuse with the 26 Jan 2026 WHO "Healthy diet" fact sheet, which only restates the headline recommendation).
**Metadata:** `{doc_type: "nutrition_general", entity: "non_sugar_sweeteners", topic: "recommendation_scope", source: "WHO", source_url: "https://apps.who.int/iris/handle/10665/353064", last_verified: "2023", comparison_group: "sugar_vs_sweetener"}`

---

## Chunk 8b
**Topic:** Non-Sugar Sweeteners — Evidence Summary (Body Weight & NCD Risk)

**Short-term RCTs (adults, mostly ≤3 months):** Higher NSS intake vs. lower/no intake associated with modest body weight reduction (MD −0.71 kg, low certainty) but no significant BMI effect. Subgroup analysis shows this effect is driven by reduced energy intake when NSS *directly replaces* sugar, not an inherent metabolic property of NSS — effect became statistically non-significant (MD −0.61 kg) and the BMI effect disappeared entirely when trials specifically tested habitual sugar-consumers switching to NSS. In trials that included a water-comparator arm, water performed as well as or better than NSS-sweetened beverages for weight outcomes.

**Long-term prospective cohort studies (adults, follow-up 2–30 yrs):** Higher NSS intake associated with increased BMI, a 76% increase in risk of incident obesity, 23–34% increased risk of type 2 diabetes, 32% increased risk of CVD (stroke +19%, hypertension +13%), 10% increased all-cause mortality, and 19% increased CVD mortality. All very-low to low certainty. Reverse causation and confounding by baseline body weight could not be ruled out, but WHO's review concluded the associations are not solely attributable to these biases.

**Children:** Evidence much more limited. One well-conducted RCT found reduced body fatness measures, but this did not hold when combined with a second trial; observational studies found no significant body-fatness associations. Some evidence (2 RCTs) that stevia specifically reduces dental caries indicators vs. sugar — but this reflects sugar displacement, not an inherent anti-caries property of NSS.

**Pregnant women:** Very low certainty evidence overall. Higher NSS intake associated with a 25% increased risk of preterm birth (mainly late preterm, 34–37 weeks). Evidence on birth weight and offspring body fatness was inconsistent across studies.

**Source:** WHO, "Use of non-sugar sweeteners: WHO guideline," Geneva, 2023, Executive Summary and Table 1 (pp. viii-xii, 8-11).
**Last verified:** 2023.
**Metadata:** `{doc_type: "nutrition_general", entity: "non_sugar_sweeteners", topic: "evidence_body_weight_ncd", source: "WHO", source_url: "https://apps.who.int/iris/handle/10665/353064", last_verified: "2023"}`

---

## Chunk 8c
**Topic:** Non-Sugar Sweeteners — Practical Implications for Product Assessment

**Core rationale:** WHO's undesirable-effects weighting is heavier for NSS specifically because a reduction in free sugars intake can be achieved *without* NSS (fruit, unsweetened alternatives) — i.e. NSS aren't the only route to the same health goal, so their uncertain long-term risk profile isn't offset by a unique benefit only they can provide.

**Relevant for product-comparison / "diet" queries:** Replacing sugar with NSS does not, per WHO, automatically make a product healthier. Because NSS have no nutritional value and are frequently used in otherwise highly processed foods, overall dietary quality is often "largely unaffected" by the substitution. This is the key caveat to surface whenever a user asks something like "is [product] a healthier choice because it's sugar-free."

**Labeling/consumer-awareness gap:** Evidence cited in the guideline indicates many consumers are unaware which products contain NSS and generally struggle to interpret nutrient-declaration labels. Relevant design implication: the chatbot should proactively flag NSS presence as a [REGULATORY]/[INTERPRETATION]-typed claim rather than assuming the user already knows a product contains them.

**ADI note — do not conflate with the FSSAI regulatory sub-base:** This guideline evaluates *health outcomes* at NSS intake levels already within the JECFA-set Acceptable Daily Intake (ADI). It is not a safety/toxicology or permitted-limit guideline. The FSSAI regulatory KB (additive permitted levels, labeling thresholds) answers a different question — "is this legal/safe to sell at this dose" vs. "does habitual consumption at safe doses have downstream health effects." Keep these as separate entities even though both get pulled into "should I worry about this sweetener" queries.

**Source:** WHO, "Use of non-sugar sweeteners: WHO guideline," Geneva, 2023, pp. 1-2, 12, 17-18.
**Last verified:** 2023.
**Metadata:** `{doc_type: "nutrition_general", entity: "non_sugar_sweeteners", topic: "practical_implications", source: "WHO", source_url: "https://apps.who.int/iris/handle/10665/353064", last_verified: "2023", comparison_group: "sugar_vs_sweetener"}`
**2026-08-18 note:** tagged with `comparison_group` (real, live pairing with `fssai_knowledge_base.md` Chunk 5, not just Chunk 8a's pre-existing tag) after live retrieval verification showed Chunk 8c — not 8a — is what actually surfaces in the fused candidate pool for q07-style diet-comparison queries; Chunk 8a's tag was left in place but doesn't match anything currently in the pool for the tested query. See `PHASE3_TESTING_LOG.md` for the Finding this fixes.

---

## Chunk 9
**Note:** New — recovered this session, was missing from the Project's copy.
**Topic:** Trans Fat — Mechanism and Product-Relevant Food Sources

**Mechanism:** Industrially-produced trans fat is formed by partially hydrogenating vegetable oil (PHO), making it solid at room temperature and shelf-stable. In the body, trans fat raises LDL ("bad") cholesterol while lowering HDL ("good") cholesterol — the combination that drives its cardiovascular risk. Trans fat has no known health benefit, unlike saturated fat which at least serves some structural/energy role.

**Product categories where PHO commonly appears:** margarine, vegetable shortening, Vanaspati ghee, fried foods and doughnuts, baked goods (crackers, biscuits, pies, cakes, wafers), and pre-mixed products (pancake mix, hot chocolate mix). PHO's trans fat content itself varies 10-60% of the oil, averaging 25-45%.

**Relevance:** Useful for [INTERPRETATION] claims explaining *why* a product's "vegetable oil" or "vanaspati" ingredient is a trans-fat red flag, not just citing the number on the nutrition label.

**Source:** WHO, "REPLACE Trans Fat: Frequently Asked Questions," WHO/NMH/NHD/18.7, May 2018, p.1.
**Last verified:** 2018-05 (original publication)
**Metadata:** `{doc_type: "nutrition_general", entity: "trans_fat", topic: "mechanism_and_sources", source: "WHO"}`

---

## Chunk 10
**Note:** New — recovered this session, was missing from the Project's copy.
**Topic:** Trans Fat — Frying/Heating Is a Minor Contributor Relative to PHO Ingredients

**Finding:** Heating and frying oil at high temperatures does increase trans fat content, but only modestly (~3.6g/100g increase on average) compared to the trans fat already present in partially hydrogenated oils (25-45% of the oil by weight). Baking, boiling, and grilling show no evidence of increasing trans fat. Practically: a product's use of PHO as a listed ingredient is a far bigger driver of trans fat content than whether the product itself was fried.

**Relevance:** Prevents an [INTERPRETATION] overreach like "this product is fried, so it's high in trans fat" — the ingredient (PHO presence) is the primary signal, not the cooking method.

**Source:** WHO, "REPLACE Trans Fat: Frequently Asked Questions," WHO/NMH/NHD/18.7, May 2018, p.2.
**Last verified:** 2018-05 (original publication)
**Metadata:** `{doc_type: "nutrition_general", entity: "trans_fat", topic: "frying_vs_phos", source: "WHO"}`

---

## Chunk 11
**Note:** New — recovered this session, was missing from the Project's copy.
**Topic:** Sodium — Evidence Quality and Scope of the WHO Recommendation

**Evidence strength:** The relationship between sodium intake and blood pressure is backed by **high-quality** evidence (meta-analysis of 36 RCTs: −3.39 mmHg systolic, −1.54 mmHg diastolic with reduced sodium). The relationship between sodium and harder outcomes — all-cause mortality, cardiovascular disease, coronary heart disease — is **lower-quality** (very low, from cohort studies) and in several cases inconclusive; only stroke risk and fatal CHD showed a statistically significant direct association with higher sodium. WHO's <2g/day recommendation rests on blood pressure as a validated proxy/biomarker for these harder outcomes, not on direct high-quality mortality data.

**Practical implication for answer-typing:** A claim like "reducing sodium in this product would lower your risk of a heart attack" should be tagged [INTERPRETATION] (proxy-based inference), not [FACT] — the direct CVD-outcome evidence is weak; only the blood-pressure link is strong.

**No adverse effects found:** Reduced sodium intake showed no significant adverse effect on blood lipids, catecholamine levels, or renal function in adults (high-quality evidence, studies ≥4 weeks); results were even suggestive of a mild renal benefit.

**Source:** WHO, "Guideline: Sodium intake for adults and children," 2012, pp.2-3, 11-14 and Annex 1 (GRADE tables).
**Last verified:** 2012 (original publication)
**Metadata:** `{doc_type: "nutrition_general", entity: "sodium", topic: "evidence_quality", source: "WHO"}`

---

## Chunk 12
**Note:** New — recovered this session, was missing from the Project's copy.
**Topic:** Sodium-Potassium Interaction

**Guidance:** If an individual meets both the WHO sodium recommendation (<2g/day) and the WHO potassium recommendation (≥3510mg/day, i.e. ≥90mmol/day), the resulting sodium:potassium molar ratio is approximately 1:1, which WHO considers beneficial for blood pressure. Potassium is increased mainly through fresh fruit and vegetables. The two recommendations are meant to be applied together, not sodium reduction alone.

**Relevance:** Useful for comparative/interpretive queries where a product is high in sodium but also naturally potassium-rich (e.g. certain vegetable- or legume-based snacks), to avoid a flat "high sodium = bad" claim without this context.

**Source:** WHO, "Guideline: Sodium intake for adults and children," 2012, pp.3, 19.
**Last verified:** 2012 (original publication)
**Metadata:** `{doc_type: "nutrition_general", entity: "sodium", topic: "potassium_interaction", source: "WHO"}`
