export default function ProductPageSkeleton() {
  return (
    <div id="product-view" aria-hidden="true">
      <div id="product-content">
        <div className="pdp-topbar">
          <span className="pdp-back">← Back</span>
        </div>

        <div className="pdp-hero-wrap">
          <div className="skeleton-block prod-media pdp-hero" />
        </div>

        <div className="pdp-body">
          <div className="gallery-strip">
            {Array.from({ length: 4 }, (_, i) => (
              <div key={i} className="skeleton-block gallery-thumb" />
            ))}
          </div>

          <div className="skeleton-block skeleton-line" style={{ width: 90, height: 18, borderRadius: 5, marginTop: 12 }} />
          <div className="skeleton-block skeleton-line" style={{ width: "50%", height: 12, marginTop: 12 }} />
          <div className="skeleton-block skeleton-line" style={{ width: "75%", height: 22, marginTop: 8 }} />
          <div className="skeleton-block skeleton-line" style={{ width: "30%", height: 13, marginTop: 8, marginBottom: 16 }} />
          <div className="skeleton-block" style={{ width: "100%", height: 60, borderRadius: "var(--radius-md)", marginBottom: 18 }} />
          <div className="skeleton-block" style={{ width: "100%", height: 62, borderRadius: "var(--radius-md)", marginBottom: 22 }} />
        </div>
      </div>
    </div>
  );
}
