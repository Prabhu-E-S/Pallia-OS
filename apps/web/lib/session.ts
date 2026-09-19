import type { CurrentUser } from "@/lib/api/types";

const SESSION_KEY = "pallia.session";

export interface Session {
  token: string;
  user: CurrentUser;
}

function isBrowser(): boolean {
  return typeof window !== "undefined";
}

function readRaw(): string | null {
  try {
    return isBrowser() ? window.localStorage.getItem(SESSION_KEY) : null;
  } catch {
    return null;
  }
}

export function getSession(): Session | null {
  const raw = readRaw();
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Session;
    if (!parsed.token || !parsed.user?.id) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function setSession(session: Session): void {
  if (!isBrowser()) return;
  try {
    window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  } catch {
    /* storage unavailable — session won't persist across reloads */
  }
}

export function clearSession(): void {
  if (!isBrowser()) return;
  try {
    window.localStorage.removeItem(SESSION_KEY);
  } catch {
    /* ignore */
  }
}