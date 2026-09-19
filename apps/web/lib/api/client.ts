import { clearAccessToken, getAccessToken, setAccessToken } from "@/lib/session";
import type { ApiError, TokenResponse } from "@/lib/api/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001";

/** Dispatched on window when a session cannot be refreshed after a 401. */
export const AUTH_EXPIRED_EVENT = "pallia:auth-expired";

export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  /** Multipart body; when present it is sent as-is (no JSON serialization). */
  formData?: FormData;
  token?: string | null;
  /**
   * Allow a single silent session-refresh + retry when the request returns
   * 401 (default true). Disable for the auth endpoints themselves to avoid
   * refresh loops.
   */
  refreshable?: boolean;
}

/** Error thrown for non-2xx API responses, matching the back-end envelope. */
export class ApiErrorResponse extends Error {
  readonly status: number;
  readonly code: string;
  readonly details: unknown;

  constructor(status: number, error: ApiError) {
    super(error.message);
    this.name = "ApiErrorResponse";
    this.status = status;
    this.code = error.code;
    this.details = error.details;
  }
}

let refreshing: Promise<boolean> | null = null;

async function attemptSessionRefresh(): Promise<boolean> {
  if (refreshing) return refreshing;
  refreshing = (async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/auth/refresh`, {
        method: "POST",
        credentials: "include",
        headers: { Accept: "application/json" },
      });
      if (!response.ok) return false;
      const payload = (await response.json()) as TokenResponse;
      setAccessToken(payload.access_token);
      return true;
    } catch {
      return false;
    } finally {
      refreshing = null;
    }
  })();
  return refreshing;
}

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const {
    method = "GET",
    body,
    formData,
    token,
    refreshable = true,
  } = options;

  let response = await rawFetch(path, method, body, formData, token);

  if (
    response.status === 401 &&
    refreshable &&
    (token ?? getAccessToken()) !== null &&
    !path.startsWith("/api/v1/auth/")
  ) {
    const refreshed = await attemptSessionRefresh();
    if (refreshed) {
      response = await rawFetch(path, method, body, formData, null);
    } else if (typeof window !== "undefined") {
      clearAccessToken();
      window.dispatchEvent(new Event(AUTH_EXPIRED_EVENT));
    }
  }

  if (response.status === 204) {
    return undefined as T;
  }

  let payload: unknown = null;
  const text = await response.text();
  if (text) {
    try {
      payload = JSON.parse(text);
    } catch {
      payload = null;
    }
  }

  if (!response.ok) {
    const envelope = payload as { error?: ApiError } | null;
    throw new ApiErrorResponse(
      response.status,
      envelope?.error ?? {
        code: "HTTP_ERROR",
        message: `Request failed with status ${response.status}`,
      },
    );
  }

  return payload as T;
}

function rawFetch(
  path: string,
  method: string,
  body: unknown,
  formData: FormData | undefined,
  token: string | null | undefined,
): Promise<Response> {
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined && !formData) headers["Content-Type"] = "application/json";

  const tokenValue = token ?? getAccessToken();
  if (tokenValue) headers.Authorization = `Bearer ${tokenValue}`;

  const payload =
    formData !== undefined
      ? formData
      : body !== undefined
        ? JSON.stringify(body)
        : undefined;

  return fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: payload,
    credentials: "include",
    cache: "no-store",
  });
}