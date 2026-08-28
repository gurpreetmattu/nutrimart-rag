import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "./AuthContext";
import * as api from "../api";

// Guest browsing (not logged in): cart lives in localStorage only, exactly
// as before this file learned about accounts at all -- no network calls,
// nothing changes for anyone who never signs in.
//
// Once logged in: the account's cart lives server-side (api/user_state.py,
// Postgres) so it follows the person across devices instead of staying
// stuck in one browser. React state stays the source of truth for
// rendering either way (same instant-feeling UI); it's just backed by
// different persistence underneath depending on isAuthenticated.
const CartContext = createContext(null);
const STORAGE_KEY = "nutrimart_cart";
const PERSIST_DEBOUNCE_MS = 400;

function loadLocalCart() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveLocalCart(cart) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(cart));
  } catch {
    // Storage unavailable (private browsing, quota) — cart still works in-memory.
  }
}

function clearLocalCart() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // As above — nothing to do if storage isn't available.
  }
}

export function CartProvider({ children }) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [cart, setCart] = useState(loadLocalCart);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const wasAuthenticated = useRef(false);
  const debounceTimers = useRef({});

  // The one-time transition on login: fold whatever's in this browser's
  // guest cart into the account's server cart (summed, not overwritten —
  // see structured/user_state.py::merge_cart), then switch over to the
  // server as the source of truth. On logout, revert to whatever's
  // sitting in localStorage (a fresh guest view, not the account's cart).
  useEffect(() => {
    if (authLoading) return;
    if (isAuthenticated && !wasAuthenticated.current) {
      const local = loadLocalCart();
      (async () => {
        try {
          const serverCart =
            Object.keys(local).length > 0 ? await api.mergeCart(local) : await api.fetchCart();
          clearLocalCart();
          setCart(serverCart);
        } catch {
          // Server unreachable right after login — keep showing the local
          // cart rather than blanking it; the next successful mutation
          // will retry persistence.
        }
      })();
    } else if (!isAuthenticated && wasAuthenticated.current) {
      setCart(loadLocalCart());
    }
    wasAuthenticated.current = isAuthenticated;
  }, [isAuthenticated, authLoading]);

  // Debounced per-product persistence so rapid +/- clicks collapse into
  // one request instead of flooding the API. Self-heals on failure by
  // re-fetching the authoritative server cart — checkout math depends on
  // this being right, so silently drifting isn't an option the way it
  // might be for lower-stakes state.
  const persistItem = useCallback((productId, quantity) => {
    clearTimeout(debounceTimers.current[productId]);
    debounceTimers.current[productId] = setTimeout(async () => {
      try {
        await api.setCartItem(productId, quantity);
      } catch {
        try {
          setCart(await api.fetchCart());
        } catch {
          // Network's down entirely — the optimistic local state is the
          // best-effort view until the next successful request.
        }
      }
    }, PERSIST_DEBOUNCE_MS);
  }, []);

  // Side effects (persistItem/saveLocalCart) deliberately live outside the
  // setState call rather than inside a functional updater -- an updater
  // must stay pure, and this project confirmed a real bug from violating
  // that in CompareContext.jsx's version of this same pattern (React 18
  // StrictMode double-invokes updaters in dev to catch exactly this; see
  // that file's comment). Cart happened to be masked here by persistItem's
  // debounce ref absorbing the duplicate call, but that was incidental, not
  // a deliberate safeguard -- fixed the same way for real robustness.
  const add = useCallback(
    (id) => {
      const next = { ...cart, [id]: 1 };
      setCart(next);
      if (isAuthenticated) persistItem(id, 1);
      else saveLocalCart(next);
    },
    [cart, isAuthenticated, persistItem]
  );

  const incr = useCallback(
    (id) => {
      const qty = (cart[id] || 0) + 1;
      const next = { ...cart, [id]: qty };
      setCart(next);
      if (isAuthenticated) persistItem(id, qty);
      else saveLocalCart(next);
    },
    [cart, isAuthenticated, persistItem]
  );

  const decr = useCallback(
    (id) => {
      const next = { ...cart };
      const qty = (next[id] || 0) - 1;
      if (qty <= 0) delete next[id];
      else next[id] = qty;
      setCart(next);
      if (isAuthenticated) persistItem(id, qty);
      else saveLocalCart(next);
    },
    [cart, isAuthenticated, persistItem]
  );

  // Used once, right after a successful checkout — replaces the old
  // "call decr() in a loop until empty" approach with a single clear.
  const clearCart = useCallback(async () => {
    setCart({});
    if (isAuthenticated) {
      try {
        await api.clearCartServer();
      } catch {
        // Best-effort — the order already succeeded; a stray leftover
        // server-side cart item would just get overwritten by the next
        // mutation anyway.
      }
    } else {
      clearLocalCart();
    }
  }, [isAuthenticated]);

  const totalCount = useMemo(() => Object.values(cart).reduce((a, b) => a + b, 0), [cart]);

  const openDrawer = useCallback(() => setDrawerOpen(true), []);
  const closeDrawer = useCallback(() => setDrawerOpen(false), []);
  const toggleDrawer = useCallback(() => setDrawerOpen((v) => !v), []);

  const value = useMemo(
    () => ({
      cart,
      add,
      incr,
      decr,
      clearCart,
      totalCount,
      drawerOpen,
      openDrawer,
      closeDrawer,
      toggleDrawer,
    }),
    [cart, add, incr, decr, clearCart, totalCount, drawerOpen, openDrawer, closeDrawer, toggleDrawer]
  );

  return <CartContext.Provider value={value}>{children}</CartContext.Provider>;
}

export function useCart() {
  return useContext(CartContext);
}
