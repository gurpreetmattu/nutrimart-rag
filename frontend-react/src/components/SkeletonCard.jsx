export default function SkeletonCard() {
  return (
    <div className="card skeleton-card" aria-hidden="true">
      <div className="skeleton-block card-media-skel" />
      <div className="card-body">
        <div className="skeleton-block skeleton-line" style={{ width: "40%", height: 14 }} />
        <div className="skeleton-block skeleton-line" style={{ width: "70%", height: 13, marginTop: 8 }} />
        <div className="skeleton-block skeleton-line" style={{ width: "85%", height: 13, marginTop: 6 }} />
        <div className="skeleton-block skeleton-line" style={{ width: "45%", height: 12, marginTop: 8 }} />
        <div className="skeleton-block skeleton-line" style={{ width: "55%", height: 18, marginTop: 12 }} />
        <div className="skeleton-block" style={{ width: "100%", height: 30, marginTop: 14, borderRadius: "var(--radius-sm)" }} />
      </div>
    </div>
  );
}
