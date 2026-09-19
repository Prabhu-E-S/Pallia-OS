import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { apiFetch, ApiErrorResponse, AUTH_EXPIRED_EVENT } from "@/lib/api/client";
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "@/lib/session";

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("apiFetch", () => {
  const originalFetch = globalThis.fetch;

  beforeEach(() => {
    clearAccessToken();
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("returns the response envelope on success", async () => {
    globalThis.fetch = vi.fn().mockResolvedValue(jsonResponse(200, { ok: true }));
    await expect(apiFetch("/any")).resolves.toEqual({ ok: true });
  });

  it("sends FormData as the body without a JSON content type", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(jsonResponse(201, { id: "r1", status: "DRAFT" }));
    globalThis.fetch = fetchMock;

    const audio = new Blob(["abc"], { type: "audio/webm" });
    const formData = new FormData();
    formData.append("report_id", "r1");
    formData.append("audio", audio, "report.webm");

    await expect(
      apiFetch("/api/v1/patients/p1/voice/transcribe", {
        method: "POST",
        formData,
      }),
    ).resolves.toEqual({ id: "r1", status: "DRAFT" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(String(url)).toContain("/voice/transcribe");
    expect(init.method).toBe("POST");
    expect(init.body).toBe(formData);
    expect(init.headers["Content-Type"]).toBeUndefined();
    expect(init.headers.Authorization).toBeUndefined();
  });

  it("throws ApiErrorResponse on non-2xx responses", async () => {
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(403, { error: { code: "FORBIDDEN", message: "Nope" } }),
      );
    try {
      await apiFetch("/any");
      throw new Error("should have thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiErrorResponse);
      expect(err).toMatchObject({ status: 403, code: "FORBIDDEN", message: "Nope" });
    }
  });

  it("silently refreshes and retries once after a 401", async () => {
    setAccessToken("stale-token");
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(401, { error: { code: "UNAUTHORIZED", message: "expired" } }),
      )
      .mockResolvedValueOnce(
        jsonResponse(200, {
          access_token: "fresh-token",
          token_type: "bearer",
          expires_in: 1800,
          refresh_token: "hidden",
          user: { id: "u1" },
        }),
      )
      .mockResolvedValueOnce(jsonResponse(200, { ok: true }));
    globalThis.fetch = fetchMock;

    await expect(apiFetch("/protected")).resolves.toEqual({ ok: true });
    expect(getAccessToken()).toBe("fresh-token");

    const refreshCall = fetchMock.mock.calls.find(([url]) =>
      String(url).includes("/api/v1/auth/refresh"),
    );
    expect(refreshCall).toBeDefined();
  });

  it("clears the session and emits auth-expired when refresh fails", async () => {
    setAccessToken("stale-token");
    globalThis.fetch = vi
      .fn()
      .mockResolvedValueOnce(
        jsonResponse(401, { error: { code: "UNAUTHORIZED", message: "expired" } }),
      )
      .mockResolvedValueOnce(
        jsonResponse(401, { error: { code: "UNAUTHORIZED", message: "no session" } }),
      );

    const listener = vi.fn();
    window.addEventListener(AUTH_EXPIRED_EVENT, listener);

    try {
      await apiFetch("/protected");
      throw new Error("should have thrown");
    } catch (err) {
      expect(err).toBeInstanceOf(ApiErrorResponse);
      expect(err).toMatchObject({ status: 401 });
    }

    expect(getAccessToken()).toBeNull();
    expect(listener).toHaveBeenCalledTimes(1);
    window.removeEventListener(AUTH_EXPIRED_EVENT, listener);
  });

  it("does not attempt a refresh for auth endpoints", async () => {
    setAccessToken("stale-token");
    globalThis.fetch = vi
      .fn()
      .mockResolvedValue(
        jsonResponse(401, { error: { code: "UNAUTHORIZED", message: "bad creds" } }),
      );

    try {
      await apiFetch("/api/v1/auth/login", {
        method: "POST",
        body: { email: "a", password: "b" },
      });
      throw new Error("should have thrown");
    } catch {
      /* expected */
    }

    const refreshHits = (globalThis.fetch as ReturnType<typeof vi.fn>).mock.calls.filter(
      ([url]) => String(url).includes("/api/v1/auth/refresh"),
    );
    expect(refreshHits).toHaveLength(0);
  });
});