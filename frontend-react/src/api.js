const API = "/api";

// credentials: "include" is what makes the browser send the httpOnly
// access_token cookie api/auth.py sets — every auth-aware call needs it.
// The vite dev server proxies /api so this is same-origin in dev too, but
// "include" is harmless there and required once this is ever deployed
// cross-origin.
async function authedFetch(path, options = {}) {
  return fetch(`${API}${path}`, { ...options, credentials: "include" });
}

async function throwIfNotOk(res) {
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // Non-JSON error body — keep the generic HTTP status message.
    }
    throw new Error(detail);
  }
  return res;
}

export async function signup(email, password, name) {
  const res = await authedFetch("/auth/signup", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, name }),
  });
  await throwIfNotOk(res);
  return res.json();
}

export async function login(email, password) {
  const res = await authedFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  await throwIfNotOk(res);
  return res.json();
}

export async function logout() {
  await authedFetch("/auth/logout", { method: "POST" });
}

export async function fetchMe() {
  const res = await authedFetch("/auth/me");
  if (!res.ok) return null; // 401 just means "not logged in" — not an error case here.
  return res.json();
}

export async function updateProfile(email, name) {
  const res = await authedFetch("/auth/me", {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, name }),
  });
  await throwIfNotOk(res);
  return res.json();
}

export async function changePassword(currentPassword, newPassword) {
  const res = await authedFetch("/auth/change-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ current_password: currentPassword, new_password: newPassword }),
  });
  await throwIfNotOk(res);
}

export async function checkout(items) {
  const res = await authedFetch("/checkout", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
  });
  await throwIfNotOk(res);
  return res.json();
}

export async function fetchOrders() {
  const res = await authedFetch("/orders");
  await throwIfNotOk(res);
  return res.json();
}

export async function fetchOrder(orderId) {
  const res = await authedFetch(`/orders/${orderId}`);
  await throwIfNotOk(res);
  return res.json();
}

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
