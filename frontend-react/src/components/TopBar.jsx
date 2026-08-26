import { useEffect, useRef, useState } from "react";
import { useCart } from "../context/CartContext";
import SearchBox from "./SearchBox";
import AddressPicker from "./AddressPicker";

export default function TopBar() {
  const { totalCount, toggleDrawer } = useCart();
  const [bounce, setBounce] = useState(false);
  const prevCountRef = useRef(totalCount);

  useEffect(() => {
    if (totalCount !== prevCountRef.current) {
      prevCountRef.current = totalCount;
      setBounce(true);
      const t = setTimeout(() => setBounce(false), 400);
      return () => clearTimeout(t);
    }
  }, [totalCount]);

  return (
    <header className="topbar">
      <div className="topbar-row1">
        <div className="brand">
          Nutri<span>Mart</span>
        </div>
        <AddressPicker />
        <div className="topbar-spacer" />
        <button
          className="cart-btn"
          onClick={toggleDrawer}
          aria-label={totalCount === 0 ? "Cart, empty" : `Cart, ${totalCount} item${totalCount > 1 ? "s" : ""}`}
        >
          🛒 <span className={`cart-count${totalCount === 0 ? " hidden" : ""}${bounce ? " bounce" : ""}`} aria-hidden="true">{totalCount}</span>
        </button>
      </div>
      <div className="topbar-row2">
        <SearchBox />
      </div>
    </header>
  );
}
