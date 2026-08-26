import { HashRouter, Routes, Route, useLocation } from "react-router-dom";
import { CartProvider } from "./context/CartContext";
import { ProductsProvider } from "./context/ProductsContext";
import { ChatProvider } from "./context/ChatContext";
import { ToastProvider } from "./context/ToastContext";
import { CompareProvider } from "./context/CompareContext";
import { RecentlyViewedProvider } from "./context/RecentlyViewedContext";
import TopBar from "./components/TopBar";
import ChatWidget from "./components/ChatWidget";
import CartDrawer from "./components/CartDrawer";
import CompareBar from "./components/CompareBar";
import CompareModal from "./components/CompareModal";
import Home from "./pages/Home";
import ProductPage from "./pages/ProductPage";

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
      </Routes>
    </div>
  );
}

export default function App() {
  return (
    <ToastProvider>
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
    </ToastProvider>
  );
}
