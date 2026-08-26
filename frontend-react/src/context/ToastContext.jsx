import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

// Generic, stackable toast notifications — replaces the old single
// cart-only toast in TopBar.jsx with something any component can call
// (add-to-cart confirmations, compare-limit warnings, etc).
const ToastContext = createContext(null);
const DEFAULT_DURATION = 2400;

let idCounter = 0;

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const timers = useRef(new Map());

  const dismiss = useCallback((id) => {
    setToasts((t) => t.filter((x) => x.id !== id));
    clearTimeout(timers.current.get(id));
    timers.current.delete(id);
  }, []);

  const showToast = useCallback(
    (message, { icon, duration = DEFAULT_DURATION } = {}) => {
      idCounter += 1;
      const id = idCounter;
      setToasts((t) => [...t, { id, message, icon }]);
      const timer = setTimeout(() => dismiss(id), duration);
      timers.current.set(id, timer);
      return id;
    },
    [dismiss]
  );

  const value = useMemo(() => ({ showToast, dismiss }), [showToast, dismiss]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="toast-stack" role="status" aria-live="polite">
        {toasts.map((t) => (
          <div className="toast-item" key={t.id} onClick={() => dismiss(t.id)}>
            {t.icon && <span className="toast-icon" aria-hidden="true">{t.icon}</span>}
            <span>{t.message}</span>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  return useContext(ToastContext);
}
