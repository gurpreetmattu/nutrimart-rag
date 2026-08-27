# Real RAGAS evaluation report

The `ragas` PyPI package against `ask_langchain_hybrid.py`. 18 question(s) scored, 2 skipped.

## Summary

| Metric | Mean |
|---|---|
| Faithfulness | 0.941 |
| Answer Relevancy | 0.820 |
| Context Precision | 0.940 |
| Context Recall | 0.944 |

## Per-question

| ID | Query | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|---|
| q01 | what is the FSSAI permitted limit for BHA in breakfast cereals | 1.000 | 0.941 | 1.000 | 1.000 |
| q02 | what does nature-identical flavouring mean | 0.857 | 0.897 | 1.000 | 1.000 |
| q03 | how much trans fat is allowed in vanaspati | 1.000 | 0.852 | 1.000 | 1.000 |
| q04 | can a product say low sugar | 0.667 | 0.826 | 1.000 | 1.000 |
| q05 | is Diet Coke's sweetener within the legal limit | 1.000 | 0.771 | 1.000 | 1.000 |
| q06 | what's the difference between refined and raw vegetable oil | 0.778 | 0.798 | 0.833 | 1.000 |
| q07 | should I pick the diet version instead of regular | 0.833 | 0.738 | 1.000 | 1.000 |
| q08 | is the caramel colour in this product a health concern | 1.000 | 0.736 | 1.000 | 1.000 |
| q10 | what is the exact FSSAI permitted level of DATEM in bread | 1.000 | 0.901 | 1.000 | 1.000 |
| q21 | what is the FSSAI permitted level of the sulphite preservative used in McVitie's Digestive biscuits | 1.000 | 0.789 | 1.000 | 1.000 |
| q22 | what is the FSSAI permitted limit for the colour additive used in Kurkure Masala Munch | 1.000 | 0.732 | 0.833 | 1.000 |
| q23 | is the flavour enhancer used in Yippee Magic Masala Noodles within FSSAI's permitted limit | 1.000 | 0.884 | 0.500 | 1.000 |
| q24 | what is the maximum permitted amount of the anticaking agent in Yippee Noodles' masala seasoning | 1.000 | 0.861 | 1.000 | 1.000 |
| q25 | does Diet Coke's caffeine content comply with FSSAI's caffeine regulation | 1.000 | 0.768 | 0.750 | 1.000 |
| q26 | what is the FSSAI compositional standard for curd (dahi) | 1.000 | 0.714 | 1.000 | 1.000 |
| q27 | can Britannia Brown Bread claim it has as much fibre as an apple | 1.000 | 0.883 | 1.000 | 0.000 |
| q28 | can a product claim it helps reduce cholesterol | 0.800 | 0.777 | 1.000 | 1.000 |
| q29 | why does Cadbury Dairy Milk's label mention cocoa butter equivalent, and is this compliant | 1.000 | 0.892 | 1.000 | 1.000 |

## Skipped

- **q09** (why does this ketchup need a preservative but fresh tomatoes don't): no chunks retrieved (structured-only or insufficient-evidence route)
- **q30** (is it mandatory for Kellogg's Corn Flakes to be fortified with vitamins and minerals): no chunks retrieved (structured-only or insufficient-evidence route)

## Notes

- q08's answer_relevancy was transiently `0.000` on the first full-batch pass
  (a `getaddrinfo failed` DNS blip affected several questions in that same
  run — q26-q29 failed outright the same way) — re-run individually here
  and got a normal `0.736`, confirming it was a network glitch, not a real
  scoring result. The affected questions (q08, q26, q27, q28, q29) were all
  re-scored individually after the main run and merged in above.
- q27's `context_recall = 0.000` is a real score, not an error — worth a
  closer look given `ARCHITECTURE.md`'s own documented note that this
  exact question (`q27`) has a known, previously-scoped retrieval
  instability (the corrective-retry threshold calibration issue).
