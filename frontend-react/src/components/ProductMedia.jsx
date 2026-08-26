import { useState } from "react";
import { categoryMeta } from "../categoryMeta";

// Photos live at public/images/products/<product_id>/<n>.(jpg|jpeg|png|webp)
// — numbered 1, 2, 3... per product, picked up automatically, no code
// change needed. Image #1 is used for grid/related-card thumbnails and as
// the initial hero on the product page; the product page also shows a
// thumbnail strip for every numbered image found (up to GALLERY_MAX).
// Any index/extension that 404s is treated as "doesn't exist" — the icon
// tile shows instead for #1, and a gallery thumbnail beyond what exists
// just removes itself (via onFail).

const IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"];
export const GALLERY_MAX = 10;

export function ProductPhoto({ productId, idx = 1, onFail, className = "", alt = "" }) {
  const [extIdx, setExtIdx] = useState(0);
  const [failed, setFailed] = useState(false);
  const [loaded, setLoaded] = useState(false);

  if (failed) return null;

  const src = `/images/products/${productId}/${idx}.${IMAGE_EXTENSIONS[extIdx]}`;

  return (
    <img
      className={`prod-photo${loaded ? " is-loaded" : ""} ${className}`}
      src={src}
      alt={alt}
      onLoad={() => setLoaded(true)}
      onError={() => {
        if (extIdx + 1 < IMAGE_EXTENSIONS.length) {
          setExtIdx(extIdx + 1);
        } else {
          setFailed(true);
          if (onFail) onFail();
        }
      }}
    />
  );
}

export function ProductMedia({ productId, category, extraClass = "", idx = 1, alt = "" }) {
  const meta = categoryMeta(category);
  return (
    <div
      className={`prod-media ${extraClass}`}
      style={{ background: `linear-gradient(135deg, ${meta.gradient[0]}, ${meta.gradient[1]})` }}
    >
      <svg viewBox="0 0 64 64" fill="white" className="thumb-icon" aria-hidden="true" dangerouslySetInnerHTML={{ __html: meta.icon }} />
      <ProductPhoto productId={productId} idx={idx} alt={alt} />
    </div>
  );
}
