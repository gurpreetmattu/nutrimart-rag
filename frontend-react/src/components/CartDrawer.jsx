import { useEffect, useMemo } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { useProducts } from "../context/ProductsContext";
import { ProductMedia } from "./ProductMedia";
import QtyControl from "./QtyControl";
import { priceInfo } from "../helpers";

export default function CartDrawer() {
  const { cart, drawerOpen, closeDrawer, totalCount } = useCart();
  const { products } = useProducts();
  const navigate = useNavigate();

  useEffect(() => {
    if (!drawerOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") closeDrawer();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [drawerOpen, closeDrawer]);

  const lines = useMemo(() => {
    const byId = new Map(products.map((p) => [p.product_id, p]));
    return Object.entries(cart)
      .map(([id, qty]) => {
        const product = byId.get(id);
        if (!product) return null;
        const price = priceInfo(product);
        return { product, qty, price };
      })
      .filter(Boolean);
  }, [cart, products]);

  const total = useMemo(() => lines.reduce((sum, l) => sum + l.price.price * l.qty, 0), [lines]);

  const handleCheckout = () => {
    closeDrawer();
    // ProtectedRoute handles the "not logged in" redirect-to-/login itself
    // once we navigate there, remembering /checkout as the place to return
    // to after login — no separate auth check needed here.
    navigate("/checkout");
  };

  return (
    <>
      <div className={`drawer-overlay${drawerOpen ? " show" : ""}`} onClick={closeDrawer} aria-hidden="true" />
      <div
        className={`cart-drawer${drawerOpen ? " open" : ""}`}
        role="dialog"
        aria-modal="true"
        aria-label="Your cart"
      >
        <div className="drawer-header">
          <span>Your Cart{totalCount > 0 ? ` (${totalCount})` : ""}</span>
          <button className="close-btn" onClick={closeDrawer} aria-label="Close cart">
            &times;
          </button>
        </div>

        <div className="drawer-body">
          {lines.length === 0 ? (
            <div className="empty-state">
              <span className="empty-state-icon" aria-hidden="true">🛒</span>
              <p className="empty-note">Your cart is empty.</p>
            </div>
          ) : (
            <div className="cart-lines">
              {lines.map((l) => (
                <div className="cart-line" key={l.product.product_id}>
                  <Link to={`/product/${l.product.product_id}`} onClick={closeDrawer} className="cart-line-media">
                    <ProductMedia productId={l.product.product_id} category={l.product.category} />
                  </Link>
                  <div className="cart-line-info">
                    <Link to={`/product/${l.product.product_id}`} onClick={closeDrawer} className="cart-line-name">
                      {l.product.name}
                    </Link>
                    <div className="cart-line-pack">
                      {l.product.pack_size?.value ? `${l.product.pack_size.value}${l.product.pack_size.unit || ""}` : ""}
                    </div>
                    <div className="cart-line-price">₹{l.price.price * l.qty}</div>
                  </div>
                  <QtyControl productId={l.product.product_id} size="cart" />
                </div>
              ))}
            </div>
          )}
        </div>

        {lines.length > 0 && (
          <div className="drawer-footer">
            <div className="drawer-total-row">
              <span>Total</span>
              <span className="drawer-total">₹{total}</span>
            </div>
            <button className="checkout-btn" onClick={handleCheckout}>
              Checkout
            </button>
          </div>
        )}
      </div>
    </>
  );
}
