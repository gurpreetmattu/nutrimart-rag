# Ingredient KB — Tier 2 (Base/Whole Ingredients)
**Status:** Drafted, never uploaded to the Project. This is real, usable content — not a scoping plan.

**Scope decision (made when Gurpreet delegated the call):** Tier 2 entries are short (1–2 line), identity/allergen-context only — no external regulatory citation, no [REGULATORY] claim typing needed. These exist purely so basic "what is X" retrieval succeeds instead of falling into the corrective/insufficient-evidence path, not because any of these ingredients carry real regulatory risk. Two exceptions elevated to fuller treatment (see bottom) because they carry genuine regulatory/labelling nuance that a naive answer could get wrong.

**Reasoning for the tiering (from the original session):** writing a full cited, sourced doc for something like "cardamom" or "potato" costs real authoring time for zero retrieval-safety payoff — there's no hallucination risk or regulatory ambiguity to ground, unlike Tier 1 additives (INS 635, sodium benzoate, etc.) where getting "is this safe" wrong is exactly the failure mode the typed-claim system exists to prevent.

**Metadata:** `{doc_type: "ingredient_general", tier: "2", citation_required: false}`

---

## Flours, Grains & Starches
| Ingredient | Note |
|---|---|
| Refined wheat flour (maida) | Finely milled, bran/germ removed. Wheat allergen. Low fibre vs. atta. |
| Wheat flour (atta) | Whole wheat flour, bran/germ retained. Wheat allergen. Higher fibre than maida. |
| Wheat bran | Outer husk layer of wheat, fibre-dense. Wheat allergen. |
| Wheat gluten / vital wheat gluten | Protein fraction of wheat, added for elasticity/structure. Wheat allergen. |
| Corn grits / corn meal | Coarsely or finely milled dried corn (maize). |
| Rice meal / rice flour | Milled rice, used as a base cereal or thickener. |
| Sorghum (jowar) flour | Millet-family grain flour, gluten-free on its own. |
| Bengal gram flour (besan) | Ground chickpea (chana dal) flour. |
| Gram meal | Coarser-ground chickpea/lentil meal, similar to besan. |
| Moth dal (tapary bean) flour | Flour from moth bean, a legume common in Indian namkeen. |
| Potato flakes / potato starch | Dehydrated potato used as binder/thickener. |
| Tapioca starch | Starch from cassava root, used as thickener/binder. |
| Starch (unspecified, sauces) | Generic thickening starch; source not disclosed on label. |
| Malt extract | Concentrated extract from sprouted barley, adds sweetness/flavour. May carry barley/gluten allergen. |
| Cereal extract (barley/millets/wheat) | Blended cereal extract base, common in malted drink mixes. Wheat/barley allergen. |
| Yeast | Leavening microorganism used in bread. |

## Oils & Fats
| Ingredient | Note |
|---|---|
| Refined palm oil / edible vegetable oil (palm oil) | Most common snack-frying oil in this dataset; high in saturated fat (~50%). |
| Refined palmolein | Liquid fraction of palm oil, lower melting point than whole palm oil. |
| Rice bran oil | Oil from the rice milling by-product layer; contains oryzanol. |
| Cottonseed/sunflower/groundnut/corn oil (blends) | Used interchangeably in some namkeen products as a blended frying oil. |
| Hydrogenated vegetable oil | Oil chemically hardened via hydrogenation; historically linked to trans fat, though modern FSSAI-regulated versions cap trans fat at 2% (cross-reference: trunk file Chunk 30). |
| Edible vegetable fat (unspecified) | Generic label term, source oil not disclosed. |
| Butter | Dairy fat. Milk allergen. |
| Fractionated fat | Fat separated into components by melting point, used for texture control in chocolate. |

## Sugars & Sweetening Bases
| Ingredient | Note |
|---|---|
| Sugar | Sucrose, the primary added-sugar source across nearly all products in this dataset. |
| Invert sugar syrup / invert syrup | Sucrose broken into glucose+fructose, resists crystallisation, common in biscuits. |
| Liquid glucose / glucose | Syrup-form sugar, adds sweetness and moisture retention. |
| Maltodextrin | Mildly sweet, easily digestible starch derivative; used as a bulking/carrier agent. |
| Date paste / date syrup | Whole-fruit sweetener base, used in Yogabar as the primary sweetening agent instead of refined sugar. |

## Dairy & Protein
| Ingredient | Note |
|---|---|
| Milk solids | Concentrated milk components (protein + lactose + fat), used for flavour/richness. Milk allergen. |
| Skimmed/skim milk powder | Dried, fat-reduced milk. Milk allergen. |
| Whey protein concentrate | Milk-derived protein isolate, common in protein bars. Milk allergen. |
| Milk protein concentrate | Higher-protein-density milk derivative than milk solids. Milk allergen. |
| Active culture | Live bacterial culture used to ferment milk into curd. |
| Probiotic — Lactobacillus casei Shirota | Proprietary probiotic strain specific to Yakult. |
| Soy protein crisps / texturized soy protein flakes | Processed soy protein used for texture/protein content in bars. Soy allergen. |
| Hydrolysed groundnut protein / hydrolyzed vegetable protein | Protein broken down via acid/enzyme hydrolysis for flavour intensity (savoury/umami). Peanut or soy allergen depending on source. |
| Peanut protein / peanut butter | Peanut allergen — distinct from tree nuts for allergy labelling purposes. |
| Cashew paste / cashew (whole) | Tree nut allergen. |
| Almond paste | Tree nut allergen. |
| Cocoa solids / cocoa powder | Non-fat cocoa bean component, provides chocolate flavour/colour without the fat cocoa butter provides. |
| Choco chips | Small-format chocolate pieces, composition (dark/milk) not always disclosed. |

## Salt
| Ingredient | Note |
|---|---|
| Iodised/iodized salt | Salt fortified with iodine per India's mandatory salt iodisation program. |
| Black salt (kala namak) | Rock salt with a distinct sulphurous flavour, common in Indian namkeen/chaat seasoning. |

## Spices, Aromatics & Flavour Bases
| Ingredient | Note |
|---|---|
| Whole/ground spices (red chilli, black pepper, clove, ginger, garlic, cumin, bay leaf, nutmeg, cinnamon, turmeric, mint, coriander, aniseed, fenugreek, cardamom, caraway, onion) | Standard Indian culinary spices; no additive or allergen significance individually. Covered as a group rather than per-spice entries — low retrieval value for 20+ near-identical "what is X spice" docs. |
| Mixed spices / spices and condiments (declared blend) | Manufacturer's proprietary blend, individual components not disclosed beyond the umbrella declaration. |
| Onion powder / garlic powder / tomato powder | Dehydrated, powdered vegetable forms used for shelf-stable flavouring. |

## Fruits & Vegetables
| Ingredient | Note |
|---|---|
| Concentrated mixed fruit juice (apple, orange, guava, apricot, mango, banana, lime, passion fruit, pineapple) | Fruit juice concentrate base in Real Fruit Power Juice — counts toward WHO's "free sugars" definition (`nutrition_knowledge_base.md` Chunk 1) despite being fruit-derived. |
| Cranberry | Whole dried fruit piece, used in Yogabar. |
| Dehydrated beans/carrot/onion/cabbage | Rehydratable vegetable pieces used in instant noodle seasoning sachets. |
| Rosemary extract | Natural antioxidant extract, sometimes used as a "clean label" alternative to synthetic antioxidants like INS 307b. |
| Glycerine | Humectant/sweetener, keeps protein bars moist. |

## Fortification Blends & Other
| Ingredient | Note |
|---|---|
| Vitamins (fortification blend) / Minerals (fortification blend) | Generic label terms covering a defined micronutrient mix — see individual `fortification` metadata fields already captured per-product in the structured DB (`products_compiled.json`); doesn't need separate KB grounding since exact values are already in SQL. |
| Water / carbonated water | Base liquid; carbonated version has added CO2 for fizz. |
| Caffeine | Naturally occurring or added stimulant; declared quantity in mg/100g on Coca-Cola and Diet Coke labels. |

---

## Elevated entries (more than "lite" — regulatory/labelling nuance)

### Cocoa Butter Equivalent
FSSAI labelling rules require CBE (a non-cocoa vegetable fat, typically from shea/illipe/sal, engineered to mimic cocoa butter's melting profile) to be declared **separately** from cocoa butter when both are present — it cannot be folded into a generic "fat" or "cocoa butter" line. Cadbury Dairy Milk's ingredient list demonstrates this: "Contains Cocoa Butter Equivalent in addition to Cocoa Butter" is a compliance disclosure, not marketing language. Relevant for any "is this real chocolate" interpretive query.
`{doc_type: "ingredient_general", entity: "cocoa_butter_equivalent", tier: "1.5", regulator_relevant: true}`

### Natural / Nature-Identical / Artificial Flavouring Substances
These are three distinct, FSSAI-defined labelling categories, not a spectrum of "how processed" — **natural** flavouring is extracted from a natural source; **nature-identical** is synthesised but chemically matches a compound that exists in nature; **artificial** has no natural-source counterpart. All three appear across this dataset (e.g. Parle-G declares "artificial flavouring substances (vanilla)" while Dark Fantasy uses "nature identical flavouring substances (chocolate)"). Common misconception worth pre-empting: "natural" isn't inherently safer or more regulated than "nature-identical" — both are permitted additive categories with their own compliance rules, and "artificial" isn't a red flag by itself under FSSAI. Cross-reference: this is the consumer-facing companion to the formal regulatory definitions already in the Chapter 3 addendum (REG-C3-6).
`{doc_type: "ingredient_general", entity: "flavouring_substance_categories", tier: "1.5", regulator_relevant: true}`

---

## Tier 1 status — UPDATED, this section was stale
This file previously said Tier 1 (INS-coded additives) "was never actually drafted" with an incomplete scoping table below as a placeholder. **That's no longer true.** Tier 1 was found in a separate session that hadn't been located yet at the time this file was written — it now exists as `ingredient_knowledge_base.md`, with **38 fully-written entries** (identity, function, FSSAI regulatory status, health considerations), cross-checked against all 41 unique INS codes actually declared across the 23 products. The old 16-row placeholder table that used to sit here has been removed — it was incomplete and is now superseded by the real file.

**Cross-reference note carried over correctly:** 635/627/631 (flavour enhancers) — identity and JECFA context covered in Tier 1, FSSAI-specific mg/kg limit still genuinely unverified. 150c/150d (caramel colours) — fully covered in the FSSAI trunk file. 160c (Kurkure's paprika colour), 334 (tartaric acid), 322 (lecithin), 471, 472e (DATEM) — all confirmed genuine regulatory gaps in Tier 1, correctly flagged there, not resolved here.
