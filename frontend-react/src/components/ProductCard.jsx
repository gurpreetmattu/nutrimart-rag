import { Link } from "react-router-dom";
import { ProductMedia } from "./ProductMedia";
import QtyControl from "./QtyControl";
import { useChat } from "../context/ChatContext";
import { useCompare } from "../context/CompareContext";
import { priceInfo } from "../helpers";

export default function ProductCard({ product }) {
  const { openChat } = useChat();
  const { compareIds, toggleCompare } = useCompare();
  const pack = product.pack_size && product.pack_size.value ? `${product.pack_size.value}${product.pack_size.unit || ""}` : "";
  const price = priceInfo(product);
  const href = `/product/${product.product_id}`;
  const comparing = compareIds.includes(product.product_id);

  return (
    <div className="card">
      <div className="card-media-wrap">
        <Link to={href} className="card-media-link" aria-label={`View ${product.name}`}>
          <ProductMedia productId={product.product_id} category={product.category} alt="" />
          {price.discount >= 10 && <span className="discount-badge">{price.discount}% OFF</span>}
        </Link>
        <button
          className={`compare-toggle-btn${comparing ? " active" : ""}`}
          onClick={(e) => {
            e.stopPropagation();
            toggleCompare(product.product_id);
          }}
          aria-pressed={comparing}
          aria-label={comparing ? "Remove from compare" : "Add to compare"}
        >
          {comparing ? "✓ Comparing" : "+ Compare"}
        </button>
        <div className="card-qty-slot">
          <QtyControl productId={product.product_id} productName={product.name} size="card" />
        </div>
      </div>
      <div className="card-body">
        <span className="delivery-badge">⚡ {price.deliveryMins} MINS</span>
        <div className="card-brand">{product.brand || ""}</div>
        <Link to={href} className="card-name-link">
          <div className="card-name">{product.name}</div>
        </Link>
        <div className="card-pack">{pack}</div>
        <div className="card-price-row">
          <span className="card-price">₹{price.price}</span>
          {price.discount > 0 && <span className="card-mrp">₹{price.mrp}</span>}
        </div>
        <button className="ask-link-btn" onClick={() => openChat(product.product_id, product.name)}>
          <span className="ask-icon" aria-hidden="true">💬</span> Ask about this
        </button>
      </div>
    </div>
  );
}
