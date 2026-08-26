import { createContext, useCallback, useContext, useMemo, useState } from "react";

// Cart state is cosmetic only — no real checkout exists in this app.
// Persisted to localStorage purely so a page refresh doesn't visibly break
// the illusion of a working cart; there is no server-side cart or order.
const CartContext = createContext(null);
const STORAGE_KEY = "nutrimart_cart";

function loadInitialCart() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function CartProvider({ children }) {
  const [cart, setCart] = useState(loadInitialCart);
  const [drawerOpen, setDrawerOpen] = useState(false);

  const persist = useCallback((next) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
    } catch {
      // Storage unavailable (private browsing, quota) — cart still works in-memory.
    }
    return next;
  }, []);

  const add = useCallback((id) => setCart((c) => persist({ ...c, [id]: 1 })), [persist]);
  const incr = useCallback((id) => setCart((c) => persist({ ...c, [id]: (c[id] || 0) + 1 })), [persist]);
  const decr = useCallback((id) => {
    setCart((c) => {
      const next = { ...c };
      next[id] = (next[id] || 0) - 1;
      if (next[id] <= 0) delete next[id];
      return persist(next);
    });
  }, [persist]);

  const totalCount = useMemo(() => Object.values(cart).reduce((a, b) => a + b, 0), [cart]);

  const openDrawer = useCallback(() => setDrawerOpen(true), []);
  const closeDrawer = useCallback(() => setDrawerOpen(false), []);
  const toggleDrawer = useCallback(() => setDrawerOpen((v) => !v), []);

  const value = useMemo(
    () => ({ cart, add, incr, decr, totalCount, drawerOpen, openDrawer, closeDrawer, toggleDrawer }),
    [cart, add, incr, decr, totalCount, drawerOpen, openDrawer, closeDrawer, toggleDrawer]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  return useContext(CartContext);
}
