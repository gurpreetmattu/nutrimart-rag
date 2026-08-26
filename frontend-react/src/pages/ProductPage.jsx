import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { fetchProduct } from "../api";
import { useProducts } from "../context/ProductsContext";
import { useChat } from "../context/ChatContext";
import { useRecentlyViewed } from "../context/RecentlyViewedContext";
import { ProductMedia, ProductPhoto, GALLERY_MAX } from "../components/ProductMedia";
import QtyControl from "../components/QtyControl";
import ProductPageSkeleton from "../components/ProductPageSkeleton";
import { categoryLabel } from "../categoryMeta";
import { priceInfo, titleCase, nutritionLabel, nutritionUnit } from "../helpers";

export default function ProductPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { products } = useProducts();
  const { openChat } = useChat();
  const { recordView } = useRecentlyViewed();

  const [product, setProduct] = useState(null);
  const [notFound, setNotFound] = useState(false);
  const [heroIdx, setHeroIdx] = useState(1);
  const [failedGallery, setFailedGallery] = useState(() => new Set());

  useEffect(() => {
    let cancelled = false;
    setProduct(null);
    setNotFound(false);
    setHeroIdx(1);
    setFailedGallery(new Set());
    window.scrollTo(0, 0);
    fetchProduct(id).then((p) => {
      if (cancelled) return;
      if (!p) setNotFound(true);
      else {
        setProduct(p);
        recordView(id);
      }
    });
    return () => {
      cancelled = true;
    };
  }, [id, recordView]);

  if (notFound) {
    return (
      <div id="product-view">
        <div id="product-content">
          <p className="empty-note">Product not found.</p>
        </div>
      </div>
    );
  }

  if (!product) {
    return <ProductPageSkeleton />;
  }

  const p = product;
  const pack = p.pack_size && p.pack_size.value ? `${p.pack_size.value}${p.pack_size.unit || ""}` : "—";
  const nutrition = (p.nutrition && p.nutrition.values) || {};
  const basis = p.nutrition && p.nutrition.basis ? titleCase(p.nutrition.basis) : "Per Serving";
  const contains = p.allergens_contains || [];
  const mayContain = p.allergens_may_contain || [];
  const hasAllergenInfo = contains.length > 0 || mayContain.length > 0;
  const price = priceInfo(p);
  const related = products.filter((o) => o.category === p.category && o.product_id !== p.product_id).slice(0, 8);
  const galleryIndices = Array.from({ length: GALLERY_MAX }, (_, i) => i + 1).filter((i) => !failedGallery.has(i));

  return (
    <div id="product-view">
      <div id="product-content">
        <div className="pdp-topbar">
          <button className="pdp-back" onClick={() => navigate(-1)}>
            ← Back
          </button>
          <span className="pdp-topbar-title">{categoryLabel(p.category)}</span>
        </div>

        <div className="pdp-hero-wrap">
          <ProductMedia
            key={heroIdx}
            productId={p.product_id}
            category={p.category}
            extraClass="pdp-hero"
            idx={heroIdx}
            alt={p.name}
          />
          {price.discount >= 10 && <span className="discount-badge pdp-discount-badge">{price.discount}% OFF</span>}
        </div>

        <div className="pdp-body">
          {galleryIndices.length > 1 && (
            <div className="gallery-strip" role="group" aria-label={`${p.name} photos`}>
              {galleryIndices.map((i) => (
                <button
                  key={i}
                  className={`gallery-thumb${i === heroIdx ? " active" : ""}`}
                  onClick={() => setHeroIdx(i)}
                  aria-label={`View photo ${i} of ${p.name}`}
                  aria-pressed={i === heroIdx}
                >
                  <ProductPhoto
                    productId={p.product_id}
                    idx={i}
                    onFail={() => setFailedGallery((prev) => new Set(prev).add(i))}
                  />
                </button>
              ))}
            </div>
          )}

          <span className="delivery-badge">⚡ Delivery in {price.deliveryMins} mins</span>
          <div className="pdp-brand">{p.brand || ""}</div>
          <h1 className="pdp-name">{p.name}</h1>
          <div className="pdp-pack">{pack}</div>

          <div className="pdp-price-row">
            <div>
              <span className="pdp-price">₹{price.price}</span>
              {price.discount > 0 && <span className="pdp-mrp">MRP ₹{price.mrp}</span>}
              {price.discount > 0 && <span className="pdp-discount-pct">{price.discount}% OFF</span>}
            </div>
            <QtyControl productId={p.product_id} productName={p.name} size="pdp" />
          </div>

          <button className="ask-cta" onClick={() => openChat(p.product_id, p.name)}>
            <span className="ask-cta-icon">✨</span>
            <span>
              <strong>Ask NutriMart AI about this product</strong>
              <small>Ingredients, allergens, FSSAI compliance, and more</small>
            </span>
            <span className="ask-cta-arrow">→</span>
          </button>

          <div className="pdp-highlights">
            <div className="highlight-chip">
              <span className="hl-label">Category</span>
              <span className="hl-value">{categoryLabel(p.category)}</span>
            </div>
            <div className="highlight-chip">
              <span className="hl-label">Pack Size</span>
              <span className="hl-value">{pack}</span>
            </div>
            <div className="highlight-chip">
              <span className="hl-label">FSSAI License</span>
              <span className="hl-value">{p.fssai_license || "—"}</span>
            </div>
          </div>

          {hasAllergenInfo && (
            <div className="allergen-callout">
              <div className="allergen-callout-title">⚠ Allergen Information</div>
              {contains.length > 0 && (
                <div className="allergen-line">
                  <strong>Contains:</strong> {contains.map((a) => titleCase(a)).join(", ")}
                </div>
              )}
              {mayContain.length > 0 && (
                <div className="allergen-line">
                  <strong>May contain:</strong> {mayContain.map((a) => titleCase(a)).join(", ")}
                </div>
              )}
            </div>
          )}

          {p.description && (
            <div className="pdp-section">
              <div className="section-title">Description</div>
              <div className="description-text">{p.description}</div>
            </div>
          )}

          <div className="pdp-section">
            <div className="section-title">Ingredients</div>
            <div className="ingredients-text">{p.ingredients_raw || "Not available"}</div>
          </div>

          <div className="pdp-section">
            <div className="section-title">Nutritional Information ({basis})</div>
            <div className="nutrition-table">
              {Object.keys(nutrition).length ? (
                Object.entries(nutrition).map(([k, v]) => (
                  <div className="fact-row" key={k}>
                    <span className="fact-label">{nutritionLabel(k)}</span>
                    <span className="fact-value">
                      {String(v)}
                      {nutritionUnit(k)}
                    </span>
                  </div>
                ))
              ) : (
                <span className="muted-note">No nutrition data</span>
              )}
            </div>
          </div>

          {related.length > 0 && (
            <div className="pdp-section">
              <div className="section-title">You may also like</div>
              <div className="related-scroll">
                {related.map((r) => (
                  <Link className="related-card" key={r.product_id} to={`/product/${r.product_id}`}>
                    <ProductMedia productId={r.product_id} category={r.category} extraClass="related-media" />
                    <div className="related-name">{r.name}</div>
                    <div className="related-price">₹{priceInfo(r).price}</div>
                  </Link>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
