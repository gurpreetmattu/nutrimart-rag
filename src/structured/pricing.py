"""
structured/pricing.py — server-side port of frontend-react's
src/helpers.js::priceInfo(). Deliberately kept byte-for-byte identical in
algorithm (same FNV-1a hash, same category rates, same bulk-discount curve)
so a price shown in the UI always matches what checkout actually charges.

This is the one place a price is treated as authoritative: /api/checkout
computes it here from product_id/category/pack_size rather than trusting
any price the client sends, since a client-submitted price is a classic
tampering vector. There's still no real pricing data in this project (see
helpers.js's own comment) — this is a deterministic, cosmetic number, not
sourced pricing.
"""

CATEGORY_RATE_PER_100 = {
    "beverages": 8,
    "biscuits": 22,
    "bread_bakery": 11,
    "breakfast_cereal": 55,
    "chips_namkeen": 30,
    "chocolate_confectionery": 105,
    "dairy": 7,
    "dairy_probiotic": 32,
    "health_drink": 34,
    "instant_noodles": 20,
    "protein_bar": 115,
    "sauces_ketchup": 22,
}
DEFAULT_RATE_PER_100 = 20
REFERENCE_SIZE = 100
BULK_DISCOUNT_EXPONENT = 0.22


def _round_half_up(x: float) -> int:
    # Python's round() is banker's-rounding (round-half-to-even); JS's
    # Math.round() always rounds half up. Matching JS exactly here (not
    # just "close enough") so a price never silently differs by 1 between
    # what the cart displays and what checkout charges.
    import math
    return math.floor(x + 0.5)


def _hash_str(s: str) -> int:
    # JS keeps h as a SIGNED 32-bit int throughout (Math.imul's return
    # type) and only applies Math.abs() once, at the very end. abs() of a
    # negative two's-complement value is NOT the same number as reading
    # those same bits as unsigned (e.g. bit pattern 0xFFFFFFFF is -1
    # signed -> abs 1, but 4294967295 unsigned) — so the sign flip has to
    # happen before the final abs, not be skipped via unsigned masking
    # throughout. Confirmed as a real bug live: masking-only produced a
    # checkout price (28) that didn't match the cart's displayed price (22)
    # for the same product on the very first end-to-end test.
    h = 2166136261
    for ch in s:
        h ^= ord(ch)
        h = (h * 16777619) & 0xFFFFFFFF
    if h >= 0x80000000:
        h -= 0x100000000
    return abs(h)


def price_for(product_id: str, category: str | None, pack_size: dict | None) -> int:
    """Returns the price in rupees (post-discount), matching helpers.js::priceInfo().price."""
    h = _hash_str(product_id or "")

    pack_value = (pack_size or {}).get("value")
    size = pack_value if isinstance(pack_value, (int, float)) and pack_value > 0 else REFERENCE_SIZE
    base_rate = CATEGORY_RATE_PER_100.get(category, DEFAULT_RATE_PER_100)

    per_unit_rate = base_rate * (REFERENCE_SIZE / size) ** BULK_DISCOUNT_EXPONENT
    jitter = 0.88 + (h % 25) / 100
    mrp = max(10, _round_half_up((per_unit_rate * size / 100) * jitter))

    discount = 5 + (h % 31)
    price = max(10, _round_half_up(mrp * (100 - discount) / 100))
    return price
