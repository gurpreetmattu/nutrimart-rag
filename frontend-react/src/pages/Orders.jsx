import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { fetchOrders, fetchOrder } from "../api";
import { ProductMedia } from "../components/ProductMedia";

function formatDate(iso) {
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    });
  } catch {
    return iso;
  }
}

function OrderCard({ order }) {
  return (
    <div className="order-card">
      <div className="order-card-header">
        <div>
          <div className="order-card-id">Order #{order.order_id.slice(0, 8)}</div>
          <div className="order-card-date">{formatDate(order.placed_at)}</div>
        </div>
        <div className="order-card-total">₹{order.total_amount}</div>
      </div>
      <div className="order-card-items">
        {order.items.map((item) => (
          <div className="order-item-row" key={item.product_id}>
            <ProductMedia productId={item.product_id} category={item.category} extraClass="order-item-media" />
            <span className="order-item-name">{item.name} <span className="order-item-qty">× {item.quantity}</span></span>
            <span className="order-item-total">₹{item.unit_price * item.quantity}</span>
          </div>
        ))}
      </div>
      <span className="order-status-badge">{order.status}</span>
    </div>
  );
}

export default function Orders() {
  const { orderId } = useParams();
  const [orders, setOrders] = useState(null);
  const [single, setSingle] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setError(null);
    if (orderId) {
      fetchOrder(orderId)
        .then((o) => !cancelled && setSingle(o))
        .catch((e) => !cancelled && setError(e.message));
    } else {
      fetchOrders()
        .then((o) => !cancelled && setOrders(o))
        .catch((e) => !cancelled && setError(e.message));
    }
    return () => {
      cancelled = true;
    };
  }, [orderId]);

  if (error) {
    return (
      <div className="orders-page">
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">⚠️</span>
          <p className="empty-note">{error}</p>
          <Link to={orderId ? "/orders" : "/"} className="pill-link">
            {orderId ? "View all orders" : "Back to Home"}
          </Link>
        </div>
      </div>
    );
  }

  if (orderId) {
    return (
      <div className="orders-page">
        <div className="order-confirm-hero">
          <span className="order-confirm-check" aria-hidden="true">✓</span>
          <h1 className="checkout-title">Order confirmed</h1>
          <p className="empty-note">We've got it — check back here for status updates.</p>
        </div>
        {single ? <OrderCard order={single} /> : <p className="empty-note">Loading…</p>}
        <Link to="/orders" className="pill-link">View all orders</Link>
      </div>
    );
  }

  return (
    <div className="orders-page">
      <h1 className="checkout-title">Your orders</h1>
      {orders === null ? (
        <p className="empty-note">Loading…</p>
      ) : orders.length === 0 ? (
        <div className="empty-state">
          <span className="empty-state-icon" aria-hidden="true">📦</span>
          <p className="empty-note">No orders yet.</p>
          <Link to="/" className="pill-link">Start shopping</Link>
        </div>
      ) : (
        <div className="orders-list">
          {orders.map((o) => (
            <OrderCard key={o.order_id} order={o} />
          ))}
        </div>
      )}
    </div>
  );
}
