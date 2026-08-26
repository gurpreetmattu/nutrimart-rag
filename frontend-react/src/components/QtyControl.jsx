import { useCart } from "../context/CartContext";
import { useToast } from "../context/ToastContext";

export default function QtyControl({ productId, productName, size = "" }) {
  const { cart, add, incr, decr } = useCart();
  const { showToast } = useToast();
  const qty = cart[productId] || 0;

  if (qty === 0) {
    return (
      <button
        className={`add-btn ${size}`}
        onClick={(e) => {
          e.stopPropagation();
          add(productId);
          showToast(productName ? `Added "${productName}" to cart` : "Added to cart", { icon: "🛒" });
        }}
        aria-label="Add to cart"
      >
        ADD
      </button>
    );
  }

  return (
    <div className={`qty-stepper ${size}`}>
      <button
        onClick={(e) => {
          e.stopPropagation();
          decr(productId);
        }}
        aria-label="Decrease quantity"
      >
        −
      </button>
      <span aria-live="polite">{qty}</span>
      <button
        onClick={(e) => {
          e.stopPropagation();
          incr(productId);
        }}
        aria-label="Increase quantity"
      >
        +
      </button>
    </div>
  );
}
