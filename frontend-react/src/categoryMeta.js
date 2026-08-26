// The backend's `category` values are DB-friendly snake_case
// (e.g. "chocolate_confectionery") — CATEGORY_META gives each one a
// human label, a two-tone gradient, and a small hand-picked SVG glyph.
// This renders behind the real product photo and is what shows if no
// photo file exists yet for that product_id, or the photo fails to load.

const SHADE = "rgba(15,23,42,.22)";
const SHADE_STRONG = "rgba(15,23,42,.32)";

export const CATEGORY_META = {
  beverages: {
    label: "Beverages",
    gradient: ["#38bdf8", "#0369a1"],
    icon: `<path d="M23 4h18v9l4 6v33a4 4 0 0 1-4 4H23a4 4 0 0 1-4-4V19l4-6V4z"/>
           <rect x="23" y="4" width="18" height="6" fill="${SHADE}"/>
           <path d="M19 30h26v4H19z" fill="${SHADE}"/>`,
  },
  biscuits: {
    label: "Biscuits & Cookies",
    gradient: ["#f0b429", "#a15c07"],
    icon: `<circle cx="20" cy="24" r="11"/>
           <circle cx="34" cy="34" r="11"/>
           <circle cx="27" cy="46" r="9"/>
           <circle cx="18" cy="21" r="1.6" fill="${SHADE_STRONG}"/>
           <circle cx="24" cy="27" r="1.6" fill="${SHADE_STRONG}"/>
           <circle cx="32" cy="31" r="1.6" fill="${SHADE_STRONG}"/>
           <circle cx="30" cy="43" r="1.6" fill="${SHADE_STRONG}"/>`,
  },
  bread_bakery: {
    label: "Bakery",
    gradient: ["#e0975b", "#8a4b21"],
    icon: `<path d="M8 34c0-14 8-22 24-22s24 8 24 22c0 6-4 9-9 9H17c-5 0-9-3-9-9z"/>
           <path d="M8 34h48v9a5 5 0 0 1-5 5H13a5 5 0 0 1-5-5v-9z"/>
           <path d="M8 35h48" stroke="${SHADE_STRONG}" stroke-width="2"/>
           <path d="M22 22v10M32 19v13M42 22v10" stroke="${SHADE}" stroke-width="2.5" fill="none" stroke-linecap="round"/>`,
  },
  breakfast_cereal: {
    label: "Breakfast Cereal",
    gradient: ["#fbbf24", "#b45309"],
    icon: `<path d="M10 28h44a2 2 0 0 1 2 2c0 12-10 22-24 22S8 42 8 30a2 2 0 0 1 2-2z"/>
           <path d="M10 28h44" stroke="${SHADE_STRONG}" stroke-width="2"/>
           <circle cx="24" cy="34" r="2" fill="${SHADE}"/>
           <circle cx="32" cy="38" r="2" fill="${SHADE}"/>
           <circle cx="40" cy="34" r="2" fill="${SHADE}"/>
           <path d="M44 14l6-6" stroke="white" stroke-width="3" stroke-linecap="round"/>
           <ellipse cx="47" cy="11" rx="4" ry="6" transform="rotate(40 47 11)"/>`,
  },
  chips_namkeen: {
    label: "Chips & Namkeen",
    gradient: ["#eab308", "#92400e"],
    icon: `<path d="M18 8h28l4 40a4 4 0 0 1-4 4.4c-2-.4-3.5-1.4-6-1.4s-4 1.4-6.5 1.4-4-1.4-6.5-1.4-4 1.4-6.5 1.4A4 4 0 0 1 14 48L18 8z"/>
           <path d="M18 8l3-4h22l3 4" fill="none" stroke="${SHADE_STRONG}" stroke-width="2.5"/>
           <path d="M24 20c3 3 3 6 0 9s-3 6 0 9" stroke="${SHADE}" stroke-width="2.2" fill="none" stroke-linecap="round"/>
           <path d="M34 18c3 3 3 6 0 9s-3 6 0 9" stroke="${SHADE}" stroke-width="2.2" fill="none" stroke-linecap="round"/>`,
  },
  chocolate_confectionery: {
    label: "Chocolate & Confectionery",
    gradient: ["#a9714a", "#4a2c17"],
    icon: `<rect x="9" y="18" width="46" height="28" rx="4"/>
           <g stroke="${SHADE_STRONG}" stroke-width="2">
             <path d="M24 18v28M40 18v28M9 32h46"/>
           </g>`,
  },
  dairy: {
    label: "Dairy",
    gradient: ["#7dd3fc", "#2563eb"],
    icon: `<path d="M24 6h16v9l5 5v34a3 3 0 0 1-3 3H22a3 3 0 0 1-3-3V20l5-5V6z"/>
           <rect x="24" y="6" width="16" height="5" fill="${SHADE}"/>
           <path d="M19 30h26" stroke="${SHADE_STRONG}" stroke-width="2.5"/>`,
  },
  dairy_probiotic: {
    label: "Probiotic Dairy",
    gradient: ["#34d399", "#047857"],
    icon: `<path d="M27 5h10v7l3 4v33a4 4 0 0 1-4 4H28a4 4 0 0 1-4-4V16l3-4V5z"/>
           <path d="M22 30h20" stroke="${SHADE_STRONG}" stroke-width="2"/>
           <circle cx="20" cy="20" r="2.4" fill="${SHADE}"/>
           <circle cx="45" cy="27" r="1.8" fill="${SHADE}"/>
           <circle cx="42" cy="15" r="1.6" fill="${SHADE}"/>`,
  },
  health_drink: {
    label: "Health Drinks",
    gradient: ["#c084fc", "#6d28d9"],
    icon: `<path d="M18 10h22l-2 40a5 5 0 0 1-5 5H25a5 5 0 0 1-5-5L18 10z"/>
           <rect x="16" y="6" width="26" height="6" rx="2"/>
           <path d="M21 24h16M22 32h14" stroke="${SHADE_STRONG}" stroke-width="2.2"/>`,
  },
  instant_noodles: {
    label: "Instant Noodles",
    gradient: ["#fb923c", "#c2410c"],
    icon: `<path d="M10 28h44c1 10-8 21-22 21S9 38 10 28z"/>
           <path d="M10 28h44" stroke="${SHADE_STRONG}" stroke-width="2"/>
           <path d="M22 18c2 3-2 5 0 8M32 15c2 3-2 5 0 8M42 18c2 3-2 5 0 8" stroke="${SHADE}" stroke-width="2.2" fill="none" stroke-linecap="round"/>`,
  },
  protein_bar: {
    label: "Protein Bars",
    gradient: ["#4ade80", "#15803d"],
    icon: `<path d="M17 22l4-5 6 3 30 16-4 5-6-3-30-16z"/>
           <path d="M21 17l-8-4-2 6 7 4M45 34l8 4 2-6-7-4"/>
           <path d="M24 24l24 13" stroke="${SHADE_STRONG}" stroke-width="2" stroke-linecap="round"/>`,
  },
  sauces_ketchup: {
    label: "Sauces & Ketchup",
    gradient: ["#f87171", "#b91c1c"],
    icon: `<path d="M28 6h8v6l4 3v6l3 3v29a4 4 0 0 1-4 4H25a4 4 0 0 1-4-4V24l3-3v-6l4-3V6z"/>
           <rect x="28" y="4" width="8" height="4"/>
           <path d="M21 34h22" stroke="${SHADE_STRONG}" stroke-width="2.2"/>`,
  },
};

export const DEFAULT_META = {
  label: "Grocery",
  gradient: ["#94a3b8", "#475569"],
  icon: `<rect x="12" y="14" width="40" height="36" rx="5"/><path d="M12 26h40" stroke="${SHADE_STRONG}" stroke-width="2"/>`,
};

export function categoryMeta(cat) {
  return CATEGORY_META[cat] || DEFAULT_META;
}

export function categoryLabel(cat) {
  if (!cat) return "Uncategorized";
  return categoryMeta(cat).label;
}
