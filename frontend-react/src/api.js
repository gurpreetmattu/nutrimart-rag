const API = "/api";

export async function fetchProducts() {
  const res = await fetch(`${API}/products`);
  return res.json();
}

export async function fetchProduct(productId) {
  const res = await fetch(`${API}/products/${productId}`);
  if (!res.ok) return null;
  return res.json();
}

export async function postChat(query, productId, sessionId) {
  const res = await fetch(`${API}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, product_id: productId, session_id: sessionId }),
  });
  if (!res.ok) {
    // A 429 (api/security.py's rate limiter) is a real, distinct case from
    // "backend is down" — surface it as such instead of the generic error
    // ChatContext.jsx's catch block would otherwise show for any failure.
    if (res.status === 429) {
      const retryAfter = res.headers.get("Retry-After");
      throw new Error(`RATE_LIMITED:${retryAfter || ""}`);
    }
    throw new Error(`HTTP ${res.status}`);
  }
  return res.json();
}
