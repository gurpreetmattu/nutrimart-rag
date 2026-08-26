import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { useToast } from "./ToastContext";

// Client-side product comparison tray. Deliberately not persisted to
// localStorage (unlike cart/recently-viewed) — this is a transient
// "working set" tool, not something a user expects to survive a reload.
const CompareContext = createContext(null);
const MAX_COMPARE = 4;

export function CompareProvider({ children }) {
  const [compareIds, setCompareIds] = useState([]);
  const [modalOpen, setModalOpen] = useState(false);
  const { showToast } = useToast();

  const toggleCompare = useCallback(
    (productId) => {
      setCompareIds((prev) => {
        if (prev.includes(productId)) return prev.filter((id) => id !== productId);
        if (prev.length >= MAX_COMPARE) {
          showToast(`You can compare up to ${MAX_COMPARE} products at once.`, { icon: "⚖️" });
          return prev;
        }
        return [...prev, productId];
      });
    },
    [showToast]
  );

  const removeFromCompare = useCallback((productId) => {
    setCompareIds((prev) => prev.filter((id) => id !== productId));
  }, []);

  const clearCompare = useCallback(() => setCompareIds([]), []);
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
