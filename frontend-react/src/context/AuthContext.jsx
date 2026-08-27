import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import * as api from "../api";

// Identity lives server-side in the httpOnly cookie api/auth.py sets — this
// context never stores a token, only the user profile it gets back from
// /api/auth/me. On mount it asks the server "am I logged in?" once; a 401
// there just means logged-out, not an error (see api.js::fetchMe).
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    api.fetchMe().then((u) => {
      if (!cancelled) {
        setUser(u);
        setLoading(false);
      }
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const signup = useCallback(async (email, password, name) => {
    const u = await api.signup(email, password, name);
    setUser(u);
    return u;
  }, []);

  const login = useCallback(async (email, password) => {
    const u = await api.login(email, password);
    setUser(u);
    return u;
  }, []);

  const logout = useCallback(async () => {
    await api.logout();
    setUser(null);
  }, []);

  const updateProfile = useCallback(async (email, name) => {
    const u = await api.updateProfile(email, name);
    setUser(u);
    return u;
  }, []);

  const changePassword = useCallback(async (currentPassword, newPassword) => {
    await api.changePassword(currentPassword, newPassword);
  }, []);

  const value = useMemo(
    () => ({ user, loading, isAuthenticated: !!user, signup, login, logout, updateProfile, changePassword }),
    [user, loading, signup, login, logout, updateProfile, changePassword]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
