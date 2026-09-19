/**
 * In-memory access-token store.
 *
 * Tokens intentionally live only in JS memory, never in localStorage or
 * cookies: after a full page load the access token is gone and the auth
 * provider re-establishes the session from the HttpOnly refresh cookie
 * (`/auth/refresh`). The refresh token itself is never visible to JS.
 */

let accessToken: string | null = null;

export function getAccessToken(): string | null {
  return accessToken;
}

export function setAccessToken(token: string | null): void {
  accessToken = token;
}

export function clearAccessToken(): void {
  accessToken = null;
}