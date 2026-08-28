import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import { useToast } from "./ToastContext";
import { useAuth } from "./AuthContext";
import * as api from "../api";

// Same guest-localStorage / logged-in-server split as CartContext.jsx.
// Originally this was deliberately NOT persisted anywhere (a "transient
// working set" — see git history) but per-account persistence was asked
// for explicitly, so that design is superseded here; guest browsing still
// gets no persistence at all (no localStorage, matching the original
// transient-by-default feel) until there's an account to attach it to.
const CompareContext = createContext(null);
const STORAGE_KEY = "nutrimart_compare";
const MAX_COMPARE = 4;

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
    // Storage unavailable — compare tray still works in-memory for this tab.
  }
}

function clearLocalStorageOnly() {
  try {
    localStorage.removeItem(STORAGE_KEY);
  } catch {
    // As above.
  }
}

export function CompareProvider({ children }) {
  const { isAuthenticated, loading: authLoading } = useAuth();
  const [compareIds, setCompareIds] = useState(loadLocal);
  const [modalOpen, setModalOpen] = useState(false);
  const { showToast } = useToast();
  const wasAuthenticated = useRef(false);

  useEffect(() => {
    if (authLoading) return;
    if (isAuthenticated && !wasAuthenticated.current) {
      const local = loadLocal();
      (async () => {
        try {
          const merged = local.length > 0 ? await api.mergeCompare(local) : await api.fetchCompare();
          clearLocalStorageOnly();
          setCompareIds(merged);
        } catch {
          // Keep the local view if the server isn't reachable right now.
        }
      })();
    } else if (!isAuthenticated && wasAuthenticated.current) {
      setCompareIds(loadLocal());
    }
    wasAuthenticated.current = isAuthenticated;
  }, [isAuthenticated, authLoading]);

  // Side effects (the api.* calls) deliberately live outside the setState
  // call, not inside a functional updater -- an updater function must stay
  // pure, and React 18 StrictMode double-invokes it in dev specifically to
  // catch violations of that. This one was a real bug, not just a dev-mode
  // nuisance: the impure updater fired api.toggleCompareServer() twice for
  // one click, and the second call 500'd against the (user_id, product_id)
  // primary key in Postgres (see structured/user_state.py::toggle_compare's
  // own comment on the matching backend fix).
  const toggleCompare = useCallback(
    (productId) => {
      if (compareIds.includes(productId)) {
        const next = compareIds.filter((id) => id !== productId);
        setCompareIds(next);
        if (isAuthenticated) api.toggleCompareServer(productId).catch(() => {});
        else saveLocal(next);
        return;
      }
      if (compareIds.length >= MAX_COMPARE) {
        showToast(`You can compare up to ${MAX_COMPARE} products at once.`, { icon: "⚖️" });
        return;
      }
      const next = [...compareIds, productId];
      setCompareIds(next);
      if (isAuthenticated) api.toggleCompareServer(productId).catch(() => {});
      else saveLocal(next);
    },
    [compareIds, isAuthenticated, showToast]
  );

  const removeFromCompare = useCallback(
    (productId) => {
      const next = compareIds.filter((id) => id !== productId);
      setCompareIds(next);
      if (isAuthenticated) api.removeFromCompareServer(productId).catch(() => {});
      else saveLocal(next);
    },
    [compareIds, isAuthenticated]
  );

  const clearCompare = useCallback(() => {
    setCompareIds([]);
    if (isAuthenticated) api.clearCompareServer().catch(() => {});
    else clearLocalStorageOnly();
  }, [isAuthenticated]);

  const openCompareModal = useCallback(() => setModalOpen(true), []);
  const closeCompareModal = useCallback(() => setModalOpen(false), []);

  const value = useMemo(
    () => ({
      compareIds,
      toggleCompare,
      removeFromCompare,
      clearCompare,
      modalOpen,
      openCompareModal,
      closeCompareModal,
      maxCompare: MAX_COMPARE,
    }),
    [compareIds, toggleCompare, removeFromCompare, clearCompare, modalOpen, openCompareModal, closeCompareModal]
  );

  return <CompareContext.Provider value={value}>{children}</CompareContext.Provider>;
}

export function useCompare() {
  return useContext(CompareContext);
}
