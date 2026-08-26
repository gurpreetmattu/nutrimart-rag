# Real RAGAS evaluation report

Real `ragas` PyPI package (not the hand-rolled equivalent) against `ask_langchain_hybrid.py`. 18 question(s) scored, 2 skipped.

## Summary

| Metric | Mean |
|---|---|
| Faithfulness | 0.712 |
| Answer Relevancy | 0.812 |
| Context Precision | 0.954 |
| Context Recall | 1.000 |

## Per-question

| ID | Query | Faithfulness | Answer Relevancy | Context Precision | Context Recall |
|---|---|---|---|---|---|
| q01 | what is the FSSAI permitted limit for BHA in breakfast cereals | 1.000 | 0.941 | 1.000 | 1.000 |
| q02 | what does nature-identical flavouring mean | 0.857 | 0.885 | 1.000 | 1.000 |
| q03 | how much trans fat is allowed in vanaspati | 1.000 | 0.852 | 1.000 | 1.000 |
| q04 | can a product say low sugar | 1.000 | 0.836 | 1.000 | 1.000 |
| q05 | is Diet Coke's sweetener within the legal limit | 0.429 | 0.772 | 1.000 | 1.000 |
| q06 | what's the difference between refined and raw vegetable oil | 0.692 | 0.796 | 0.833 | 1.000 |
| q07 | should I pick the diet version instead of regular | 0.333 | 0.727 | 1.000 | 1.000 |
| q08 | is the caramel colour in this product a health concern | 1.000 | 0.732 | 1.000 | 1.000 |
| q10 | what is the exact FSSAI permitted level of DATEM in bread | 1.000 | 0.897 | 1.000 | 1.000 |
| q21 | what is the FSSAI permitted level of the sulphite preservative used in McVitie's Digestive biscuits | 0.500 | 0.780 | 1.000 | 1.000 |
| q22 | what is the FSSAI permitted limit for the colour additive used in Kurkure Masala Munch | 0.200 | 0.732 | 0.833 | 1.000 |
| q23 | is the flavour enhancer used in Yippee Magic Masala Noodles within FSSAI's permitted limit | 0.600 | 0.884 | 0.500 | 1.000 |
| q24 | what is the maximum permitted amount of the anticaking agent in Yippee Noodles' masala seasoning | 0.500 | 0.839 | 1.000 | 1.000 |
| q25 | does Diet Coke's caffeine content comply with FSSAI's caffeine regulation | 0.667 | 0.711 | 1.000 | 1.000 |
| q26 | what is the FSSAI compositional standard for curd (dahi) | 1.000 | 0.708 | 1.000 | 1.000 |
| q27 | can Britannia Brown Bread claim it has as much fibre as an apple | 0.667 | 0.836 | 1.000 | 1.000 |
| q28 | can a product claim it helps reduce cholesterol | 0.800 | 0.798 | 1.000 | 1.000 |
| q29 | why does Cadbury Dairy Milk's label mention cocoa butter equivalent, and is this compliant | 0.571 | 0.892 | 1.000 | 1.000 |

## Skipped

- **q09** (why does this ketchup need a preservative but fresh tomatoes don't): no chunks retrieved (structured-only or insufficient-evidence route)
- **q30** (is it mandatory for Kellogg's Corn Flakes to be fortified with vitamins and minerals): no chunks retrieved (structured-only or insufficient-evidence route)