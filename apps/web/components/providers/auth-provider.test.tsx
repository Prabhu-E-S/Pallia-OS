import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { AuthProvider, useAuth } from "@/components/providers/auth-provider";
import { ApiErrorResponse } from "@/lib/api/client";
import { getAccessToken } from "@/lib/session";
import type { TokenResponse } from "@/lib/api/types";

const USER = {
  id: "u1",
  email: "admin@pallia.demo",
  full_name: "Ananya Sharma",
  role: "ADMIN",
  organization_id: "o1",
  organization_name: "Maple Grove Home Care",
  status: "ACTIVE",
  permissions: ["patient.read", "patient.create"],
} as const;

const TOKEN_RESPONSE: TokenResponse = {
  access_token: "fresh-token",
  token_type: "bearer",
  expires_in: 1800,
  refresh_token: "refresh-secret",
  user: { ...USER, permissions: [...USER.permissions] },
};

let mockAuthApi = vi.fn();

vi.mock("@/lib/api/auth", () => ({
  authApi: () => mockAuthApi(),
}));

function Probe() {
  const { user, status, login, logout, hasPermission, canAccess } = useAuth();
  return (
    <div>
      <span data-testid="status">{status}</span>
      <span data-testid="email">{user?.email ?? "—"}</span>
      <span data-testid="read">{String(hasPermission("patient.read"))}</span>
      <span data-testid="any">{String(canAccess("visit.read", "patient.read"))}</span>
      <button onClick={() => void login("admin@pallia.demo", "pallia123")}>login</button>
      <button onClick={() => void logout()}>logout</button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    mockAuthApi = vi.fn();
  });

  it("restores the session via refresh when the access token is gone", async () => {
    mockAuthApi.mockReturnValue({
      me: vi.fn().mockRejectedValueOnce(
        new ApiErrorResponse(401, { code: "UNAUTHORIZED", message: "expired" }),
      ).mockResolvedValue({ ...USER, permissions: [...USER.permissions] }),
      refresh: vi.fn().mockResolvedValue(TOKEN_RESPONSE),
      login: vi.fn(),
      logout: vi.fn().mockResolvedValue(undefined),
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });
    expect(screen.getByTestId("email")).toHaveTextContent("admin@pallia.demo");
    expect(getAccessToken()).toBe("fresh-token");
    expect(screen.getByTestId("read")).toHaveTextContent("true");
    expect(screen.getByTestId("any")).toHaveTextContent("true");
  });

  it("reports unauthenticated when neither token nor refresh work", async () => {
    mockAuthApi.mockReturnValue({
      me: vi.fn().mockRejectedValue(
        new ApiErrorResponse(401, { code: "UNAUTHORIZED", message: "expired" }),
      ),
      refresh: vi.fn().mockRejectedValue(
        new ApiErrorResponse(401, { code: "UNAUTHORIZED", message: "no session" }),
      ),
      login: vi.fn(),
      logout: vi.fn().mockResolvedValue(undefined),
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("unauthenticated");
    });
    expect(getAccessToken()).toBeNull();
  });

  it("logs in with real credentials and records the user", async () => {
    mockAuthApi.mockReturnValue({
      me: vi.fn().mockRejectedValue(
        new ApiErrorResponse(401, { code: "UNAUTHORIZED", message: "expired" }),
      ),
      refresh: vi.fn().mockRejectedValue(
        new ApiErrorResponse(401, { code: "UNAUTHORIZED", message: "no session" }),
      ),
      login: vi.fn().mockResolvedValue(TOKEN_RESPONSE),
      logout: vi.fn().mockResolvedValue(undefined),
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("unauthenticated");
    });

    await fireEvent.click(screen.getByRole("button", { name: "login" }));

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });
    expect(mockAuthApi().login).toHaveBeenCalledWith("admin@pallia.demo", "pallia123");
    expect(screen.getByTestId("email")).toHaveTextContent("admin@pallia.demo");
  });

  it("clears the session on logout", async () => {
    mockAuthApi.mockReturnValue({
      me: vi.fn().mockResolvedValue({ ...USER, permissions: [...USER.permissions] }),
      refresh: vi.fn(),
      login: vi.fn().mockResolvedValue(TOKEN_RESPONSE),
      logout: vi.fn().mockResolvedValue(undefined),
    });

    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("authenticated");
    });

    await fireEvent.click(screen.getByRole("button", { name: "logout" }));

    await waitFor(() => {
      expect(screen.getByTestId("status")).toHaveTextContent("unauthenticated");
    });
    expect(mockAuthApi().logout).toHaveBeenCalledTimes(1);
    expect(getAccessToken()).toBeNull();
  });
});