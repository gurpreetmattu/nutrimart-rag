export function titleCase(s) {
  return s.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

const NUTRITION_LABELS = {
  energy_kcal: "Energy",
  protein_g: "Protein",
  carbohydrate_g: "Carbohydrate",
  total_sugars_g: "Total Sugars",
  added_sugars_g: "Added Sugars",
  total_fat_g: "Total Fat",
  saturated_fat_g: "Saturated Fat",
  trans_fat_g: "Trans Fat",
  cholesterol_mg: "Cholesterol",
  sodium_mg: "Sodium",
};

export function nutritionLabel(key) {
  if (NUTRITION_LABELS[key]) return NUTRITION_LABELS[key];
  return titleCase(key.replace(/_(g|mg|kcal)$/, ""));
}

export function nutritionUnit(key) {
  const m = key.match(/_(g|mg|kcal)$/);
  return m ? m[1] : "";
}

// This app has no real commerce backend or pricing data — these are
// deterministic, cosmetic numbers (seeded from product_id) purely so the
// UI reads like a real quick-commerce listing. Ingredients/nutrition/
// allergen data shown elsewhere is real; price and delivery time are not.
//
// Price is derived from category + pack_size (not just a product_id hash,
// which produced nonsense like a 1000g curd costing less than a 150g
// chocolate bar) — a rough ₹-per-100g/100ml rate per category, scaled by
// the product's real pack size, with a mild bulk-pricing curve (bigger
// packs cost less per unit, same as real quick-commerce) and a small
// deterministic per-product jitter so same-category items don't all sit on
// one identical curve. Rates are ballpark Indian-retail approximations,
// not sourced data — good enough for "does this look like a real catalog,"
// not meant to be quoted as real pricing.

function hashStr(s) {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return Math.abs(h);
}

const CATEGORY_RATE_PER_100 = {
  beverages: 8,
  biscuits: 22,
  bread_bakery: 11,
  breakfast_cereal: 55,
  chips_namkeen: 30,
  chocolate_confectionery: 105,
  dairy: 7,
  dairy_probiotic: 32,
  health_drink: 34,
  instant_noodles: 20,
  protein_bar: 115,
  sauces_ketchup: 22,
};
const DEFAULT_RATE_PER_100 = 20;
const REFERENCE_SIZE = 100;
const BULK_DISCOUNT_EXPONENT = 0.22;

export function priceInfo(product) {
  const productId = typeof product === "string" ? product : product?.product_id;
  const h = hashStr(productId || "");

  const packValue = product?.pack_size?.value;
  const size = typeof packValue === "number" && packValue > 0 ? packValue : REFERENCE_SIZE;
  const baseRate = CATEGORY_RATE_PER_100[product?.category] ?? DEFAULT_RATE_PER_100;

  // Larger packs cost less per unit (bulk pricing) rather than scaling
  // linearly — a flat per-unit rate would make a 1kg pack look absurdly
  // expensive next to a 100g one of the same product line.
  const perUnitRate = baseRate * Math.pow(REFERENCE_SIZE / size, BULK_DISCOUNT_EXPONENT);
  const jitter = 0.88 + (h % 25) / 100; // deterministic +/-12%
  const mrp = Math.max(10, Math.round(((perUnitRate * size) / 100) * jitter));

  const discount = 5 + (h % 31);
  const price = Math.max(10, Math.round((mrp * (100 - discount)) / 100));
  const deliveryMins = 6 + (h % 15);
  return { mrp, discount, price, deliveryMins };
}

const CLAIM_TAGS = ["FACT", "REGULATORY", "INTERPRETATION", "DERIVED CALCULATION", "UNCERTAIN"];
export const CLAIM_TAG_MAP = {
  FACT: "fact",
  REGULATORY: "regulatory",
  INTERPRETATION: "interpretation",
  "DERIVED CALCULATION": "derived",
  UNCERTAIN: "uncertain",
};

const CLAIM_TAG_RE = new RegExp(`\\[(${CLAIM_TAGS.join("|")})\\]`, "g");

// Splits a chat answer into plain-text and claim-tag segments so the UI
// can render tags as styled spans without dangerouslySetInnerHTML.
export function parseAnswer(text) {
  const parts = [];
  let last = 0;
  let m;
  CLAIM_TAG_RE.lastIndex = 0;
  while ((m = CLAIM_TAG_RE.exec(text))) {
    if (m.index > last) parts.push({ type: "text", value: text.slice(last, m.index) });
    parts.push({ type: "tag", value: m[1] });
    last = CLAIM_TAG_RE.lastIndex;
  }
  if (last < text.length) parts.push({ type: "text", value: text.slice(last) });
  return parts;
}
