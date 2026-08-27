import { HashRouter, Routes, Route, useLocation } from "react-router-dom";
import { CartProvider } from "./context/CartContext";
import { ProductsProvider } from "./context/ProductsContext";
import { ChatProvider } from "./context/ChatContext";
import { ToastProvider } from "./context/ToastContext";
import { CompareProvider } from "./context/CompareContext";
import { RecentlyViewedProvider } from "./context/RecentlyViewedContext";
import { AuthProvider } from "./context/AuthContext";
import TopBar from "./components/TopBar";
import ChatWidget from "./components/ChatWidget";
import CartDrawer from "./components/CartDrawer";
import CompareBar from "./components/CompareBar";
import CompareModal from "./components/CompareModal";
import ProtectedRoute from "./components/ProtectedRoute";
import Home from "./pages/Home";
import ProductPage from "./pages/ProductPage";
import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Checkout from "./pages/Checkout";
import Orders from "./pages/Orders";
import EditProfile from "./pages/EditProfile";
import NotFound from "./pages/NotFound";

// Keying on pathname remounts this div on every navigation, which restarts
// its CSS enter animation — a cheap crossfade without a routing-transition
// library. No exit animation (would need one), but the momentary overlap
// reads fine for a fade-up this short.
function AnimatedRoutes() {
  const location = useLocation();
  return (
    <div key={location.pathname} className="page-transition">
      <Routes location={location}>
        <Route path="/" element={<Home />} />
        <Route path="/product/:id" element={<ProductPage />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route
          path="/checkout"
          element={
            <ProtectedRoute>
              <Checkout />
            </ProtectedRoute>
          }
        />
        <Route
          path="/orders"
          element={
            <ProtectedRoute>
              <Orders />
            </ProtectedRoute>
          }
        />
        <Route
          path="/orders/:orderId"
          element={
            <ProtectedRoute>
              <Orders />
            </ProtectedRoute>
          }
        />
        <Route
          path="/account"
          element={
            <ProtectedRoute>
              <EditProfile />
            </ProtectedRoute>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <CartProvider>
          <ProductsProvider>
            <RecentlyViewedProvider>
              <CompareProvider>
                <ChatProvider>
                  <HashRouter>
                    <TopBar />
                    <AnimatedRoutes />
                    <ChatWidget />
                    <CartDrawer />
                    <CompareBar />
                    <CompareModal />
                  </HashRouter>
                </ChatProvider>
              </CompareProvider>
            </RecentlyViewedProvider>
          </ProductsProvider>
        </CartProvider>
      </AuthProvider>
    </ToastProvider>
  );
}
