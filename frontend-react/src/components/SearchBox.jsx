import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useProducts } from "../context/ProductsContext";
import { ProductMedia } from "./ProductMedia";
import { priceInfo } from "../helpers";

const MAX_SUGGESTIONS = 6;

export default function SearchBox() {
  const { products, search, setSearch } = useProducts();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);
  const containerRef = useRef(null);

  const suggestions = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return [];
    return products
      .filter((p) => p.name.toLowerCase().includes(q) || (p.brand || "").toLowerCase().includes(q))
      .slice(0, MAX_SUGGESTIONS);
  }, [products, search]);

  useEffect(() => {
    setActiveIndex(-1);
  }, [search]);

  useEffect(() => {
    function handleOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, []);

  const selectSuggestion = (p) => {
    setOpen(false);
    setSearch("");
    navigate(`/product/${p.product_id}`);
  };

  const showDropdown = open && suggestions.length > 0;

  const handleKeyDown = (e) => {
    if (!showDropdown) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActiveIndex((i) => (i + 1) % suggestions.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActiveIndex((i) => (i <= 0 ? suggestions.length - 1 : i - 1));
    } else if (e.key === "Enter") {
      if (activeIndex >= 0) {
        e.preventDefault();
        selectSuggestion(suggestions[activeIndex]);
      }
    } else if (e.key === "Escape") {
      setOpen(false);
    }
  };

  return (
    <div className="search-box" ref={containerRef}>
      <label htmlFor="product-search" className="sr-only">
        Search products
      </label>
      <input
        id="product-search"
        className="search"
        type="text"
        role="combobox"
        aria-expanded={showDropdown}
        aria-controls="search-suggestions"
        aria-autocomplete="list"
        aria-activedescendant={activeIndex >= 0 ? `suggestion-${activeIndex}` : undefined}
        placeholder="Search for atta, curd, chocolate..."
        value={search}
        onChange={(e) => {
          setSearch(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={handleKeyDown}
        autoComplete="off"
      />
      {showDropdown && (
        <ul className="search-suggestions" id="search-suggestions" role="listbox" aria-label="Product suggestions">
          {suggestions.map((p, i) => {
            const price = priceInfo(p);
            return (
              <li
                key={p.product_id}
                id={`suggestion-${i}`}
                role="option"
                aria-selected={i === activeIndex}
                className={`search-suggestion${i === activeIndex ? " active" : ""}`}
                onMouseDown={(e) => {
                  e.preventDefault();
                  selectSuggestion(p);
                }}
                onMouseEnter={() => setActiveIndex(i)}
              >
                <div className="suggestion-media">
                  <ProductMedia productId={p.product_id} category={p.category} />
                </div>
                <div className="suggestion-info">
                  <div className="suggestion-name">{p.name}</div>
                  <div className="suggestion-brand">{p.brand}</div>
                </div>
                <div className="suggestion-price">₹{price.price}</div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
