import { Link } from "react-router-dom";
import { useMemo } from "react";
import { useProducts } from "../context/ProductsContext";
import { useRecentlyViewed } from "../context/RecentlyViewedContext";
import { ProductMedia } from "./ProductMedia";
import { priceInfo } from "../helpers";

export default function RecentlyViewedRail() {
  const { products } = useProducts();
  const { ids } = useRecentlyViewed();

  const items = useMemo(() => {
    const byId = new Map(products.map((p) => [p.product_id, p]));
    return ids.map((id) => byId.get(id)).filter(Boolean);
  }, [products, ids]);

  if (items.length === 0) return null;

  return (
    <div className="recently-viewed-rail">
      <div className="section-title">Recently viewed</div>
      <div className="related-scroll">
        {items.map((p) => (
          <Link className="related-card" key={p.product_id} to={`/product/${p.product_id}`}>
            <ProductMedia productId={p.product_id} category={p.category} extraClass="related-media" />
            <div className="related-name">{p.name}</div>
            <div className="related-price">₹{priceInfo(p).price}</div>
          </Link>
        ))}
      </div>
    </div>
  );
}
