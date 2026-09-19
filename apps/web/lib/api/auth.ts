import { apiFetch } from "@/lib/api/client";
import type {
  CurrentUser,
  DeviceLoginRequest,
  DeviceLoginResponse,
} from "@/lib/api/types";

export function authApi() {
  return {
    devLogin(email: string): Promise<DeviceLoginResponse> {
      const payload: DeviceLoginRequest = { email };
      return apiFetch<DeviceLoginResponse>("/api/v1/auth/dev-login", {
        method: "POST",
        body: payload,
      });
    },

    me(token?: string | null): Promise<CurrentUser> {
      return apiFetch<CurrentUser>("/api/v1/auth/me", { token });
    },
  };
}