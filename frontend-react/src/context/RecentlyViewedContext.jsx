import { createContext, useCallback, useContext, useMemo, useState } from "react";

// Tracks product_ids the user has opened a detail page for, most-recent-
// first, deduped, capped — same cosmetic-persistence pattern as
// CartContext (localStorage only, no server-side history).
const RecentlyViewedContext = createContext(null);
const STORAGE_KEY = "nutrimart_recently_viewed";
const MAX_ITEMS = 12;

function loadInitial() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function RecentlyViewedProvider({ children }) {
  const [ids, setIds] = useState(loadInitial);

  const recordView = useCallback((productId) => {
    if (!productId) return;
    setIds((prev) => {
      const next = [productId, ...prev.filter((id) => id !== productId)].slice(0, MAX_ITEMS);
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        // Storage unavailable — history still works in-memory for this tab.
      }
      return next;
    });
  }, []);

  const value = useMemo(() => ({ ids, recordView }), [ids, recordView]);

  return <RecentlyViewedContext.Provider value={value}>{children}</RecentlyViewedContext.Provider>;
}

export function useRecentlyViewed() {
  return useContext(RecentlyViewedContext);
}
