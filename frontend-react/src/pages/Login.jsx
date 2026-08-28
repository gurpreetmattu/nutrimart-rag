import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Login() {
  const { login, isAuthenticated, loading } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const redirectTo = location.state?.from || "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // An already-logged-in visitor landing here (bookmark, back button, a
  // stale link) has nothing to do on this page — showing the form again
  // just invites confusion. Same fix as Signup.jsx.
  //
  // Redirects to `redirectTo`, NOT a hardcoded "/" — confirmed real bug:
  // this guard's condition also becomes true the instant handleSubmit's
  // own `await login(...)` resolves (isAuthenticated flips before that
  // async function's next line runs), so the component re-renders and
  // hits this early return BEFORE handleSubmit's own
  // `navigate(redirectTo, ...)` call executes. With a hardcoded "/" here,
  // that race always won and silently discarded the real destination —
  // e.g. a guest clicking Checkout, sent to /login with `from: "/checkout"`
  // state, always landed on Home after logging in instead of back at
  // checkout. Both paths must agree on the same target.
  if (!loading && isAuthenticated) {
    return <Navigate to={redirectTo} replace />;
  }

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate(redirectTo, { replace: true });
    } catch (err) {
      setError(err.message || "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="brand auth-brand">
          Nutri<span>Mart</span>
        </div>
        <h1 className="auth-title">Log in</h1>
        <p className="auth-subtitle">Welcome back — enter your details to continue.</p>
        {error && <div className="auth-error">{error}</div>}
        <label className="auth-field">
          <span>Email</span>
          <input
            type="email"
            required
            autoComplete="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </label>
        <label className="auth-field">
          <span>Password</span>
          <input
            type="password"
            required
            autoComplete="current-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>
        <button className="auth-submit" type="submit" disabled={submitting}>
          {submitting ? "Logging in…" : "Log in"}
        </button>
        <p className="auth-switch">
          New here? <Link to="/signup">Create an account</Link>
        </p>
      </form>
    </div>
  );
}
