import { useMemo, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useCart } from "../context/CartContext";
import { useProducts } from "../context/ProductsContext";
import { useToast } from "../context/ToastContext";
import { checkout } from "../api";
import { ProductMedia } from "../components/ProductMedia";
import { priceInfo } from "../helpers";

export default function Checkout() {
  const { cart, decr, incr } = useCart();
  const { products } = useProducts();
  const { showToast } = useToast();
  const navigate = useNavigate();

  const [placing, setPlacing] = useState(false);
  const [error, setError] = useState(null);

  const lines = useMemo(() => {
    const byId = new Map(products.map((p) => [p.product_id, p]));
    return Object.entries(cart)
      .map(([id, qty]) => {
        const product = byId.get(id);
        if (!product) return null;
        return { product, qty, price: priceInfo(product) };
      })
      .filter(Boolean);
  }, [cart, products]);

  const total = useMemo(() => lines.reduce((sum, l) => sum + l.price.price * l.qty, 0), [lines]);

  const handlePlaceOrder = async () => {
    setError(null);
    setPlacing(true);
    try {
      const order = await checkout(lines.map((l) => ({ product_id: l.product.product_id, quantity: l.qty })));
      // Clear the cart line by line (CartContext has no bulk-clear — this
      // mirrors what decr() already does down to zero for each line).
      lines.forEach((l) => {
        for (let i = 0; i < l.qty; i++) decr(l.product.product_id);
      });
      showToast("Order placed!", { icon: "✅" });
      navigate(`/orders/${order.order_id}`, { replace: true });
    } catch (err) {
      setError(err.message || "Could not place order");
    } finally {
      setPlacing(false);
    }
  };

  if (lines.length === 0) {
    return (
      <div className="checkout-page">
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">🛒</span>
          <p className="empty-note">Your cart is empty.</p>
          <Link to="/" className="pill-link">Continue shopping</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="checkout-page">
      <h1 className="checkout-title">Checkout</h1>
      {error && <div className="auth-error">{error}</div>}
      <div className="checkout-lines">
        {lines.map((l) => (
          <div className="cart-line" key={l.product.product_id}>
            <Link to={`/product/${l.product.product_id}`} className="cart-line-media">
              <ProductMedia productId={l.product.product_id} category={l.product.category} />
            </Link>
            <div className="cart-line-info">
              <span className="cart-line-name">{l.product.name}</span>
              <div className="cart-line-pack">
                {l.product.pack_size?.value ? `${l.product.pack_size.value}${l.product.pack_size.unit || ""}` : ""}
              </div>
              <div className="cart-line-price">
                ₹{l.price.price * l.qty} <span className="checkout-qty-label">× {l.qty}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
      <div className="checkout-summary">
        <div className="drawer-total-row">
          <span>Total</span>
          <span className="drawer-total">₹{total}</span>
        </div>
        <button className="checkout-btn" onClick={handlePlaceOrder} disabled={placing}>
          {placing ? "Placing order…" : "Place order"}
        </button>
      </div>
    </div>
  );
}
