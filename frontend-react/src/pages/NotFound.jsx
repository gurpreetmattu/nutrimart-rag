import { Link } from "react-router-dom";

// Catches any path that doesn't match a real route — previously an
// unmatched hash URL rendered a blank main area (no Route element,
// nothing shown) with no way out except the browser's back button.
export default function NotFound() {
  return (
    <div className="orders-page">
      <div className="empty-state">
        <span className="empty-state-icon" aria-hidden="true">🧭</span>
        <p className="empty-note">This page doesn't exist.</p>
        <Link to="/" className="pill-link">Back to Home</Link>
      </div>
    </div>
  );
}
