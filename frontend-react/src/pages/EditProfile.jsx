import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useToast } from "../context/ToastContext";

export default function EditProfile() {
  const { user, updateProfile, changePassword } = useAuth();
  const { showToast } = useToast();

  const [name, setName] = useState(user?.name || "");
  const [email, setEmail] = useState(user?.email || "");
  const [profileError, setProfileError] = useState(null);
  const [savingProfile, setSavingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordError, setPasswordError] = useState(null);
  const [changingPassword, setChangingPassword] = useState(false);

  const displayName = user?.name || user?.email || "";
  const initial = displayName.charAt(0).toUpperCase() || "?";

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileError(null);
    setSavingProfile(true);
    try {
      await updateProfile(email, name || null);
      showToast("Profile updated", { icon: "✅" });
    } catch (err) {
      setProfileError(err.message || "Could not update profile");
    } finally {
      setSavingProfile(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordError(null);
    if (newPassword.length < 8) {
      setPasswordError("New password must be at least 8 characters.");
      return;
    }
    setChangingPassword(true);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      showToast("Password changed", { icon: "✅" });
    } catch (err) {
      setPasswordError(err.message || "Could not change password");
    } finally {
      setChangingPassword(false);
    }
  };

  return (
    <div className="profile-page">
      <div className="profile-header">
        <span className="profile-header-avatar" aria-hidden="true">{initial}</span>
        <div className="profile-header-text">
          <div className="profile-header-name">{displayName}</div>
          <div className="profile-header-email">{user?.email}</div>
        </div>
      </div>

      <form className="profile-section" onSubmit={handleProfileSubmit}>
        <div className="profile-section-heading">
          <span className="profile-section-icon" aria-hidden="true">👤</span>
          <h2 className="profile-section-title">Your details</h2>
        </div>
        {profileError && <div className="auth-error">{profileError}</div>}
        <label className="auth-field">
          <span>Name</span>
          <input type="text" value={name} onChange={(e) => setName(e.target.value)} placeholder="Your name" />
        </label>
        <label className="auth-field">
          <span>Email</span>
          <input type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <button className="auth-submit profile-submit" type="submit" disabled={savingProfile}>
          {savingProfile ? "Saving…" : "Save changes"}
        </button>
      </form>

      <form className="profile-section" onSubmit={handlePasswordSubmit}>
        <div className="profile-section-heading">
          <span className="profile-section-icon" aria-hidden="true">🔒</span>
          <h2 className="profile-section-title">Change password</h2>
        </div>
        {passwordError && <div className="auth-error">{passwordError}</div>}
        <label className="auth-field">
          <span>Current password</span>
          <input
            type="password"
            required
            autoComplete="current-password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
          />
        </label>
        <label className="auth-field">
          <span>New password</span>
          <input
            type="password"
            required
            minLength={8}
            autoComplete="new-password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
          />
          <span className="auth-hint">At least 8 characters</span>
        </label>
        <button className="auth-submit profile-submit" type="submit" disabled={changingPassword}>
          {changingPassword ? "Changing…" : "Change password"}
        </button>
      </form>
    </div>
  );
}
