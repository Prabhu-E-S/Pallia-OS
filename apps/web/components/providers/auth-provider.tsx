"use client";

import { createContext, useCallback, useContext, useState } from "react";
import type { Session } from "@/lib/session";
import { clearSession, getSession, setSession as persistSession } from "@/lib/session";

interface AuthContextValue {
  session: Session | null;
  ready: boolean;
  login: (session: Session) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function readInitialSession(): Session | null {
  if (typeof window === "undefined") return null;
  return getSession();
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [session, setSessionState] = useState<Session | null>(readInitialSession);

  const login = useCallback((next: Session) => {
    persistSession(next);
    setSessionState(next);
  }, []);

  const logout = useCallback(() => {
    clearSession();
    setSessionState(null);
  }, []);

  return (
    <AuthContext.Provider value={{ session, ready: true, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return value;
}