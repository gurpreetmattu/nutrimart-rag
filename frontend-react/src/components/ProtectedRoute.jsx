import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

// Gates checkout/order-history the way most real storefronts do: browsing
// and cart-building need no account, placing an order or viewing history
// does. Redirects to /login and remembers where to come back to.
export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth();
  const location = useLocation();

  if (loading) return null;
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  }
  return children;
}
