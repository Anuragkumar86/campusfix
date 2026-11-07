"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, ApiError, resetCsrf, UNAUTHORIZED_EVENT } from "@/lib/api";
import type { User } from "@/types";

interface AuthState {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<User>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

/** The /api/auth/me/ endpoint is the single source of truth for identity and role. */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    api<User>("/api/auth/me/")
      .then((u) => active && setUser(u))
      .catch((e) => {
        if (!(e instanceof ApiError) || e.status !== 401) console.error(e);
        if (active) setUser(null);
      })
      .finally(() => active && setLoading(false));
    const onExpired = () => setUser(null);
    window.addEventListener(UNAUTHORIZED_EVENT, onExpired);
    return () => {
      active = false;
      window.removeEventListener(UNAUTHORIZED_EVENT, onExpired);
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    resetCsrf();
    const u = await api<User>("/api/auth/login/", { method: "POST", json: { email: email.trim(), password } });
    resetCsrf(); // Django rotates the CSRF token on login
    setUser(u);
    return u;
  }, []);

  const logout = useCallback(async () => {
    try {
      await api("/api/auth/logout/", { method: "POST" });
    } finally {
      resetCsrf();
      setUser(null);
    }
  }, []);

  const value = useMemo(() => ({ user, loading, login, logout }), [user, loading, login, logout]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
