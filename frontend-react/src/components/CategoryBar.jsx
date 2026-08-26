import { useMemo } from "react";
import { useProducts } from "../context/ProductsContext";
import { categoryLabel } from "../categoryMeta";

export default function CategoryBar() {
  const { products, category, setCategory } = useProducts();

  const cats = useMemo(() => ["all", ...new Set(products.map((p) => p.category).filter(Boolean))], [products]);

  return (
    <div className="category-bar" role="group" aria-label="Filter by category">
      {cats.map((cat) => (
        <button
          key={cat}
          className={`category-chip${cat === category ? " active" : ""}`}
          onClick={() => setCategory(cat)}
          aria-pressed={cat === category}
        >
          {cat === "all" ? "All" : categoryLabel(cat)}
        </button>
      ))}
    </div>
  );
}
