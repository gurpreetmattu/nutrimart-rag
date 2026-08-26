import { useEffect, useMemo, useState } from "react";
import { useCompare } from "../context/CompareContext";
import { fetchProduct } from "../api";
import { ProductMedia } from "./ProductMedia";
import { categoryLabel } from "../categoryMeta";
import { priceInfo, titleCase, nutritionLabel, nutritionUnit } from "../helpers";

export default function CompareModal() {
  const { compareIds, modalOpen, closeCompareModal, removeFromCompare } = useCompare();
  // The shared ProductsContext only holds list-summary fields (no
  // nutrition, and allergens only as of the dietary-filter fix) — compare
  // needs full per-product detail, so it fetches it directly, same as
  // ProductPage.jsx does for a single product.
  const [details, setDetails] = useState({});

  useEffect(() => {
    if (!modalOpen) return;
    const missing = compareIds.filter((id) => !details[id]);
    if (missing.length === 0) return;
    let cancelled = false;
    Promise.all(missing.map((id) => fetchProduct(id))).then((fetched) => {
      if (cancelled) return;
      setDetails((prev) => {
        const next = { ...prev };
        fetched.forEach((p, i) => {
          if (p) next[missing[i]] = p;
        });
        return next;
      });
    });
    return () => {
      cancelled = true;
    };
  }, [modalOpen, compareIds, details]);

  useEffect(() => {
    if (!modalOpen) return;
    const handleKeyDown = (e) => {
      if (e.key === "Escape") closeCompareModal();
    };
    document.addEventListener("keydown", handleKeyDown);
    return () => document.removeEventListener("keydown", handleKeyDown);
  }, [modalOpen, closeCompareModal]);

  const items = useMemo(
    () => compareIds.map((id) => details[id]).filter(Boolean),
    [compareIds, details]
  );

  const nutritionKeys = useMemo(() => {
    const keys = new Set();
    items.forEach((p) => Object.keys(p.nutrition?.values || {}).forEach((k) => keys.add(k)));
    return Array.from(keys);
  }, [items]);

  if (!modalOpen) return null;

  const loading = items.length < compareIds.length;

  return (
    <>
      <div className="drawer-overlay show" onClick={closeCompareModal} aria-hidden="true" />
      <div className="compare-modal" role="dialog" aria-modal="true" aria-label="Compare products">
        <div className="drawer-header">
          <span>Compare Products</span>
          <button className="close-btn" onClick={closeCompareModal} aria-label="Close compare">
            &times;
          </button>
        </div>
        <div className="compare-modal-body">
          {loading ? (
            <p className="empty-note">Loading product details…</p>
          ) : items.length === 0 ? (
            <p className="empty-note">Nothing left to compare.</p>
          ) : (
            <table className="compare-table">
              <thead>
                <tr>
                  <th className="compare-row-label"></th>
                  {items.map((p) => (
                    <th key={p.product_id}>
                      <button
                        className="compare-remove-col"
                        onClick={() => removeFromCompare(p.product_id)}
                        aria-label={`Remove ${p.name} from compare`}
                      >
                        &times;
                      </button>
                      <div className="compare-col-media">
                        <ProductMedia productId={p.product_id} category={p.category} />
                      </div>
                      <div className="compare-col-name">{p.name}</div>
                      <div className="compare-col-brand">{p.brand}</div>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td className="compare-row-label">Price</td>
                  {items.map((p) => (
                    <td key={p.product_id}>₹{priceInfo(p).price}</td>
                  ))}
                </tr>
                <tr>
                  <td className="compare-row-label">Pack Size</td>
                  {items.map((p) => (
                    <td key={p.product_id}>
                      {p.pack_size?.value ? `${p.pack_size.value}${p.pack_size.unit || ""}` : "—"}
                    </td>
                  ))}
                </tr>
                <tr>
                  <td className="compare-row-label">Category</td>
                  {items.map((p) => (
                    <td key={p.product_id}>{categoryLabel(p.category)}</td>
                  ))}
                </tr>
                {nutritionKeys.map((k) => (
                  <tr key={k}>
                    <td className="compare-row-label">{nutritionLabel(k)}</td>
                    {items.map((p) => {
                      const v = p.nutrition?.values?.[k];
                      return <td key={p.product_id}>{v === undefined ? "—" : `${v}${nutritionUnit(k)}`}</td>;
                    })}
                  </tr>
                ))}
                <tr>
                  <td className="compare-row-label">Allergens</td>
                  {items.map((p) => (
                    <td key={p.product_id}>
                      {(p.allergens_contains || []).length
                        ? p.allergens_contains.map((a) => titleCase(a)).join(", ")
                        : "None declared"}
                    </td>
                  ))}
                </tr>
              </tbody>
            </table>
          )}
        </div>
      </div>
    </>
  );
}
