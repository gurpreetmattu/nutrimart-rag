import { useProducts } from "../context/ProductsContext";

const SORT_OPTIONS = [
  { id: "relevance", label: "Relevance" },
  { id: "price_low", label: "Price: Low to High" },
  { id: "price_high", label: "Price: High to Low" },
  { id: "delivery", label: "Fastest Delivery" },
  { id: "discount", label: "Best Offers" },
];

export default function SortBar() {
  const { sort, setSort } = useProducts();

  return (
    <div className="sort-bar" role="group" aria-label="Sort products">
      <span className="sort-bar-label">Sort by</span>
      {SORT_OPTIONS.map((opt) => (
        <button
          key={opt.id}
          className={`sort-chip${sort === opt.id ? " active" : ""}`}
          onClick={() => setSort(opt.id)}
          aria-pressed={sort === opt.id}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}
