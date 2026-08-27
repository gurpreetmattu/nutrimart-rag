import { useMemo } from "react";
import { useProducts } from "../context/ProductsContext";
import CategoryBar from "../components/CategoryBar";
import SortBar from "../components/SortBar";
import ProductCard from "../components/ProductCard";
import SkeletonCard from "../components/SkeletonCard";
import RecentlyViewedRail from "../components/RecentlyViewedRail";
import WelcomeBanner from "../components/WelcomeBanner";
import PromoCarousel from "../components/PromoCarousel";
import { priceInfo } from "../helpers";

const SKELETON_COUNT = 10;

export default function Home() {
  const { products, category, search, setSearch, sort, loading } = useProducts();

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return products.filter((p) => {
      const matchesCategory = category === "all" || p.category === category;
      const matchesSearch = !q || p.name.toLowerCase().includes(q) || (p.brand || "").toLowerCase().includes(q);
      return matchesCategory && matchesSearch;
    });
  }, [products, category, search]);

  const sorted = useMemo(() => {
    if (sort === "relevance") return filtered;
    const withPrice = filtered.map((p) => ({ p, price: priceInfo(p) }));
    switch (sort) {
      case "price_low":
        withPrice.sort((a, b) => a.price.price - b.price.price);
        break;
      case "price_high":
        withPrice.sort((a, b) => b.price.price - a.price.price);
        break;
      case "delivery":
        withPrice.sort((a, b) => a.price.deliveryMins - b.price.deliveryMins);
        break;
      case "discount":
        withPrice.sort((a, b) => b.price.discount - a.price.discount);
        break;
      default:
        break;
    }
    return withPrice.map((x) => x.p);
  }, [filtered, sort]);

  return (
    <main id="home-view">
      {!search && <WelcomeBanner />}
      {!loading && products.length > 0 && !search && <PromoCarousel />}
      {!loading && products.length > 0 && !search && <RecentlyViewedRail />}
      <CategoryBar />
      {!loading && products.length > 0 && <SortBar />}
      <div className="grid">
        {loading ? (
          Array.from({ length: SKELETON_COUNT }, (_, i) => <SkeletonCard key={i} />)
        ) : sorted.length === 0 ? (
          <div className="empty-state">
            <span className="empty-state-icon" aria-hidden="true">🔍</span>
            <p className="empty-note">No products match "{search}".</p>
            <button className="pill-link" onClick={() => setSearch("")}>Clear search</button>
          </div>
        ) : (
          sorted.map((p) => <ProductCard key={p.product_id} product={p} />)
        )}
      </div>
    </main>
  );
}
