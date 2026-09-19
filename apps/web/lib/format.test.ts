import { describe, expect, it } from "vitest";
import { cn } from "@/lib/cn";
import { ageFrom, formatDate, initials, pluralize, shortName } from "@/lib/format";

describe("cn", () => {
  it("joins truthy classes and skips falsy ones", () => {
    expect(cn("a", "b", false, undefined, null, "", "c")).toBe("a b c");
  });
});

describe("formatDate", () => {
  it("formats an ISO date", () => {
    expect(formatDate("2026-09-19T10:30:00Z")).toMatch(/Sep/);
  });

  it("returns a dash for missing values", () => {
    expect(formatDate(null)).toBe("—");
    expect(formatDate(undefined)).toBe("—");
  });

  it("handles invalid dates gracefully", () => {
    expect(formatDate("not-a-date")).toBe("—");
  });
});

describe("ageFrom", () => {
  it("computes whole-year age", () => {
    const age = ageFrom("1941-03-12");
    expect(age).toBeGreaterThanOrEqual(80);
    expect(age).toBeLessThanOrEqual(119);
  });

  it("returns null for empty or invalid input", () => {
    expect(ageFrom(null)).toBeNull();
    expect(ageFrom("garbage")).toBeNull();
  });
});

describe("initials", () => {
  it("produces up to two initials", () => {
    expect(initials("Amma Lakshmi")).toBe("AL");
    expect(initials("Ravi")).toBe("R");
  });

  it("falls back for empty names", () => {
    expect(initials("")).toBe("?");
    expect(initials(null)).toBe("?");
  });
});

describe("shortName", () => {
  it("abbreviates the surname", () => {
    expect(shortName("Ravi Iyer")).toBe("Ravi I.");
  });

  it("keeps single-word names", () => {
    expect(shortName("Ravi")).toBe("Ravi");
    expect(shortName(null)).toBe("—");
  });
});

describe("pluralize", () => {
  it("handles singular, plural, and custom forms", () => {
    expect(pluralize(1, "patient")).toBe("patient");
    expect(pluralize(2, "patient")).toBe("patients");
    expect(pluralize(3, "task", "tasks")).toBe("tasks");
  });
});