import { apiFetch } from "@/lib/api/client";
import type { CurrentUser, LoginRequest, TokenResponse } from "@/lib/api/types";

export function authApi() {
  return {
    login(email: string, password: string): Promise<TokenResponse> {
      const payload: LoginRequest = { email, password };
      return apiFetch<TokenResponse>("/api/v1/auth/login", {
        method: "POST",
        body: payload,
        refreshable: false,
      });
    },

    refresh(): Promise<TokenResponse> {
      return apiFetch<TokenResponse>("/api/v1/auth/refresh", {
        method: "POST",
        refreshable: false,
      });
    },

    me(token?: string | null): Promise<CurrentUser> {
      return apiFetch<CurrentUser>("/api/v1/auth/me", { token });
    },

    logout(): Promise<void> {
      return apiFetch<void>("/api/v1/auth/logout", {
        method: "POST",
        refreshable: false,
      });
    },
  };
}