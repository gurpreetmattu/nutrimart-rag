import { useAuth } from "../context/AuthContext";

// Purely informational — no action button here. The account menu in
// TopBar is the one place "Log in" / "Your Orders" / "Edit Profile" live;
// this banner used to duplicate those same actions, which read as
// redundant (same label doing the same thing in two places on the same
// screen). Keeping it to a greeting/nudge only removes that duplication.
export default function WelcomeBanner() {
  const { user, isAuthenticated, loading } = useAuth();

  if (loading) return null;

  if (isAuthenticated) {
    const firstName = (user?.name || user?.email || "").split(" ")[0].split("@")[0];
    return (
      <div className="welcome-card">
        <span className="welcome-avatar" aria-hidden="true">{firstName.charAt(0).toUpperCase() || "🙂"}</span>
        <div className="welcome-text">
          <div className="welcome-headline">Welcome back, {firstName}!</div>
          <div className="welcome-sub">Good to see you again.</div>
        </div>
      </div>
    );
  }

  return (
    <div className="welcome-card welcome-card-guest">
      <span className="welcome-avatar welcome-avatar-guest" aria-hidden="true">👋</span>
      <div className="welcome-text">
        <div className="welcome-headline">New here?</div>
        <div className="welcome-sub">Log in (top right) for faster checkout and order history.</div>
      </div>
    </div>
  );
}
