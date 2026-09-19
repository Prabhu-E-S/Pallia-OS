import { getSession } from "@/lib/session";
import type { ApiError } from "@/lib/api/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8001";

export interface RequestOptions {
  method?: "GET" | "POST" | "PATCH" | "PUT" | "DELETE";
  body?: unknown;
  token?: string | null;
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

export async function apiFetch<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = "GET", body, token } = options;
  const headers: Record<string, string> = { Accept: "application/json" };
  if (body !== undefined) headers["Content-Type"] = "application/json";

  const tokenValue = token ?? getSession()?.token ?? null;
  if (tokenValue) headers.Authorization = `Bearer ${tokenValue}`;

  const response = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    cache: "no-store",
  });

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