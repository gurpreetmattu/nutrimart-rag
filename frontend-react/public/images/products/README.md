# Product photos

Each product gets its own subfolder named exactly `<product_id>/`, with
images numbered `1`, `2`, `3`... inside it — e.g.
`amul_dark_chocolate/1.png`, `amul_dark_chocolate/2.png`. Extensions can
be mixed within the same product (`.jpg`, `.jpeg`, `.png`, `.webp` are all
tried automatically per image). No code change needed — just add/replace
files.

- Image `1` is used as the card thumbnail (grid + related-products) and
  as the product page's initial hero image.
- Every numbered image found (up to 10 per product) shows as a clickable
  thumbnail strip under the hero on the product page — tap one to swap
  the hero image, same as a real Blinkit/Instamart product gallery.
- Missing numbers/products just fall back to the category icon tile —
  nothing breaks if a folder is missing or incomplete.

## Folder names expected (23 products)

```
amul_dark_chocolate/
amul_masti_curd/
britannia_brown_bread/
britannia_good_day_cashew/
cadbury_bournvita_chocolate_drink/
cadbury_dairy_milk/
coca_cola_original/
diet_coke/
haldirams_nagpur_aloo_bhujia/
kelloggs_chocos/
kelloggs_corn_flakes_original/
kissan_fresh_tomato_ketchup/
kurkure_masala_munch/
lays_classic_salted/
maggi_double_masala_noodles/
maggi_hot_sweet_sauce/
mcvities_digestive/
parle_g_original/
real_fruit_power_mixed_fruit_juice/
sunfeast_dark_fantasy_choco_fills/
yakult_probiotic_drink/
yippee_magic_masala_noodles/
yogabar_daily_protein_bar_dark_chocolate_cranberry/
```
