import { beforeEach, describe, expect, it } from "vitest";
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
} from "@/lib/session";

describe("access token store", () => {
  beforeEach(() => {
    clearAccessToken();
  });

  it("returns null before any token is set", () => {
    expect(getAccessToken()).toBeNull();
  });

  it("round-trips the in-memory token", () => {
    setAccessToken("jwt-abc");
    expect(getAccessToken()).toBe("jwt-abc");
  });

  it("clears the token", () => {
    setAccessToken("jwt-abc");
    clearAccessToken();
    expect(getAccessToken()).toBeNull();
  });
});