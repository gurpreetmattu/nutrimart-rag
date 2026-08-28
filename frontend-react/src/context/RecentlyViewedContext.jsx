import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "./AuthContext";
import * as api from "../api";

// Same guest-localStorage / logged-in-server split as CartContext.jsx —
// see that file's docstring for the full reasoning. Lower stakes than
// cart (nothing downstream depends on this being exactly right), so
// mutations stay simple fire-and-forget rather than debounced/self-healing.
const RecentlyViewedContext = createContext(null);
const STORAGE_KEY = "nutrimart_recently_viewed";
const MAX_ITEMS = 12;

function loadLocal() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function saveLocal(ids) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
  } catch {
    // Storage unavailable — history still works in-memory for this tab.
  }
}

function clearLocal() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // As above.
  }
}

export function RecentlyViewedProvider({ children }) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [ids, setIds] = useState(loadLocal);
  const wasAuthenticated = useRef(false);

  useEffect(() => {
    if (authLoading) return;
    if (isAuthenticated && !wasAuthenticated.current) {
      const local = loadLocal();
      (async () => {
        try {
          const merged = local.length > 0 ? await api.mergeRecentlyViewed(local) : await api.fetchRecentlyViewed();
          clearLocal();
          setIds(merged);
        } catch {
          // Keep the local view if the server isn't reachable right now.
        }
      })();
    } else if (!isAuthenticated && wasAuthenticated.current) {
      setIds(loadLocal());
    }
    wasAuthenticated.current = isAuthenticated;
  }, [isAuthenticated, authLoading]);

  // Side effect deliberately lives outside the setState call, not inside a
  // functional updater -- see CartContext.jsx/CompareContext.jsx's matching
  // comment for why (a real bug in CompareContext.jsx's version of this
  // pattern, caught by React 18 StrictMode's dev-mode double-invoke).
  // record_view()'s UPSERT made a duplicate call here harmless rather than
  // a 500, but that was incidental, not a deliberate safeguard.
  const recordView = useCallback(
    (productId) => {
      if (!productId) return;
      const next = [productId, ...ids.filter((id) => id !== productId)].slice(0, MAX_ITEMS);
      setIds(next);
      if (isAuthenticated) {
        api.recordView(productId).catch(() => {
          // Fire-and-forget — a missed write here just means this one
          // view doesn't show up until the next successful one.
        });
      } else {
        saveLocal(next);
      }
    },
    [ids, isAuthenticated]
  );

  const value = useMemo(() => ({ ids, recordView }), [ids, recordView]);

  return <RecentlyViewedContext.Provider value={value}>{children}</RecentlyViewedContext.Provider>;
}

export function useRecentlyViewed() {
  return useContext(RecentlyViewedContext);
}
