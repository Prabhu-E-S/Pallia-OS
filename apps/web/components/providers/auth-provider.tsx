"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { authApi } from "@/lib/api/auth";
import { ApiErrorResponse, AUTH_EXPIRED_EVENT } from "@/lib/api/client";
import { clearAccessToken, setAccessToken } from "@/lib/session";
import type { CurrentUser } from "@/lib/api/types";

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  user: CurrentUser | null;
  status: AuthStatus;
  /** True once the initial session check (including refresh) has finished. */
  ready: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  canAccess: (...permissions: string[]) => boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  useEffect(() => {
    let cancelled = false;

    async function bootstrap(): Promise<void> {
      try {
        let currentUser: CurrentUser;
        try {
          currentUser = await authApi().me();
        } catch (err) {
          if (err instanceof ApiErrorResponse && err.status === 401) {
            const response = await authApi().refresh();
            setAccessToken(response.access_token);
            currentUser = await authApi().me();
          } else {
            throw err;
          }
        }
        if (cancelled) return;
        setUser(currentUser);
        setStatus("authenticated");
      } catch {
        clearAccessToken();
        if (!cancelled) setStatus("unauthenticated");
      }
    }

    void bootstrap();

    function handleExpired(): void {
      setAccessToken(null);
      setUser(null);
      setStatus("unauthenticated");
    }
    if (typeof window !== "undefined") {
      window.addEventListener(AUTH_EXPIRED_EVENT, handleExpired);
    }
    return () => {
      cancelled = true;
      if (typeof window !== "undefined") {
        window.removeEventListener(AUTH_EXPIRED_EVENT, handleExpired);
      }
    };
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    const response = await authApi().login(email, password);
    setAccessToken(response.access_token);
    setUser(response.user);
    setStatus("authenticated");
  }, []);

  const logout = useCallback(async () => {
    try {
      await authApi().logout();
    } catch {
      /* session may already be expired; local state still must clear */
    }
    clearAccessToken();
    setUser(null);
    setStatus("unauthenticated");
  }, []);

  const hasPermission = useCallback(
    (permission: string) => Boolean(user?.permissions.includes(permission)),
    [user],
  );

  const canAccess = useCallback(
    (...permissions: string[]) => permissions.some((permission) => hasPermission(permission)),
    [hasPermission],
  );

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status,
      ready: status !== "loading",
      login,
      logout,
      hasPermission,
      canAccess,
    }),
    [user, status, login, logout, hasPermission, canAccess],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return value;
}