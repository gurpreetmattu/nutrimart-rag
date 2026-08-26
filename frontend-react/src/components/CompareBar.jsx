import { useMemo } from "react";
import { useCompare } from "../context/CompareContext";
import { useProducts } from "../context/ProductsContext";
import { ProductMedia } from "./ProductMedia";

export default function CompareBar() {
  const { compareIds, removeFromCompare, clearCompare, openCompareModal, maxCompare } = useCompare();
  const { products } = useProducts();

  const items = useMemo(() => {
    const byId = new Map(products.map((p) => [p.product_id, p]));
    return compareIds.map((id) => byId.get(id)).filter(Boolean);
  }, [products, compareIds]);

  if (items.length === 0) return null;

  return (
    <div className="compare-bar" role="region" aria-label="Product comparison tray">
      <div className="compare-bar-items">
        {items.map((p) => (
          <div className="compare-bar-item" key={p.product_id}>
            <ProductMedia productId={p.product_id} category={p.category} />
            <button
              className="compare-bar-remove"
              onClick={() => removeFromCompare(p.product_id)}
              aria-label={`Remove ${p.name} from compare`}
            >
              &times;
            </button>
          </div>
        ))}
        {Array.from({ length: maxCompare - items.length }, (_, i) => (
          <div className="compare-bar-slot" key={`slot-${i}`} aria-hidden="true" />
        ))}
      </div>
      <span className="compare-bar-count">{items.length}/{maxCompare} selected</span>
      <button className="compare-bar-clear" onClick={clearCompare}>
        Clear
      </button>
      <button className="compare-bar-cta" onClick={openCompareModal} disabled={items.length < 2}>
        Compare Now
      </button>
    </div>
  );
}
