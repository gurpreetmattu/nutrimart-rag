import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { fetchProducts } from "../api";

const ProductsContext = createContext(null);

export function ProductsProvider({ children }) {
  const [products, setProducts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [category, setCategory] = useState("all");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("relevance");

  useEffect(() => {
    let cancelled = false;
    fetchProducts().then((data) => {
      if (cancelled) return;
      setProducts(data);
      setLoading(false);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo(
    () => ({ products, loading, category, setCategory, search, setSearch, sort, setSort }),
    [products, loading, category, search, sort]
  );

  return <ProductsContext.Provider value={value}>{children}</ProductsContext.Provider>;
}

export function useProducts() {
  return useContext(ProductsContext);
}
