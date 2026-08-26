import { useEffect, useRef, useState } from "react";

// Cosmetic only, like the mock pricing elsewhere in this app — there is no
// real address book or delivery backend. Just gives the delivery pill a
// working dropdown instead of static text, matching a real quick-commerce
// app's topbar.
const ADDRESSES = [
  { id: "home", label: "Home", detail: "HSR Layout, Bengaluru", mins: 8 },
  { id: "work", label: "Work", detail: "Koramangala, Bengaluru", mins: 14 },
  { id: "other", label: "Other", detail: "Indiranagar, Bengaluru", mins: 11 },
];

export default function AddressPicker() {
  const [open, setOpen] = useState(false);
  const [selectedId, setSelectedId] = useState("home");
  const containerRef = useRef(null);

  const selected = ADDRESSES.find((a) => a.id === selectedId) || ADDRESSES[0];

  useEffect(() => {
    function handleOutside(e) {
      if (containerRef.current && !containerRef.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, []);

  return (
    <div className="address-picker" ref={containerRef}>
      <button
        className="delivery-pill"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span className="delivery-time">{selected.mins} mins</span>
        <span className="delivery-location">
          {selected.label} - {selected.detail} ▾
        </span>
      </button>
      {open && (
        <ul className="address-dropdown" role="listbox" aria-label="Delivery address">
          {ADDRESSES.map((a) => (
            <li
              key={a.id}
              role="option"
              aria-selected={a.id === selectedId}
              className={`address-option${a.id === selectedId ? " active" : ""}`}
              onClick={() => {
                setSelectedId(a.id);
                setOpen(false);
              }}
            >
              <span className="address-option-label">{a.label}</span>
              <span className="address-option-detail">{a.detail}</span>
              <span className="address-option-mins">{a.mins} mins</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
