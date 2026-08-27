import { useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { useAuth } from "../context/AuthContext";
import SearchBox from "./SearchBox";
import AddressPicker from "./AddressPicker";

const AUTH_ROUTES = new Set(["/login", "/signup"]);

export default function TopBar() {
  const { totalCount, toggleDrawer } = useCart();
  const { user, isAuthenticated, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [bounce, setBounce] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const prevCountRef = useRef(totalCount);
  // Hide the "Log in" account button while already on the login/signup
  // page itself — showing it there duplicated the page's own heading and
  // submit button with the same action.
  const onAuthPage = AUTH_ROUTES.has(location.pathname);

  useEffect(() => {
    if (totalCount !== prevCountRef.current) {
      prevCountRef.current = totalCount;
      setBounce(true);
      const t = setTimeout(() => setBounce(false), 400);
      return () => clearTimeout(t);
    }
  }, [totalCount]);

  useEffect(() => {
    if (!menuOpen) return;
    const close = () => setMenuOpen(false);
    document.addEventListener("click", close);
    return () => document.removeEventListener("click", close);
  }, [menuOpen]);

  const handleLogout = async () => {
    setMenuOpen(false);
    await logout();
    navigate("/");
  };

  return (
    <header className="topbar">
      <div className="topbar-row1">
        <Link to="/" className="brand" aria-label="NutriMart home">
          Nutri<span>Mart</span>
        </Link>
        <AddressPicker />
        <div className="topbar-spacer" />
        <div className="account-menu-wrap" onClick={(e) => e.stopPropagation()}>
          {isAuthenticated ? (
            <>
              <button className="account-btn" onClick={() => setMenuOpen((v) => !v)}>
                👤 <span className="account-name">{user?.name || user?.email}</span>
              </button>
              {menuOpen && (
                <div className="account-menu">
                  <Link to="/account" className="account-menu-item" onClick={() => setMenuOpen(false)}>
                    <span className="account-menu-icon" aria-hidden="true">✏️</span> Edit Profile
                  </Link>
                  <Link to="/orders" className="account-menu-item" onClick={() => setMenuOpen(false)}>
                    <span className="account-menu-icon" aria-hidden="true">📦</span> Your Orders
                  </Link>
                  <div className="account-menu-divider" role="separator" />
                  <button className="account-menu-item" onClick={handleLogout}>
                    <span className="account-menu-icon" aria-hidden="true">🚪</span> Log out
                  </button>
                </div>
              )}
            </>
          ) : (
            !onAuthPage && (
              <Link to="/login" className="account-btn">
                👤 <span className="account-name">Log in</span>
              </Link>
            )
          )}
        </div>
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
