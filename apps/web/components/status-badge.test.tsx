import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Badge } from "@/components/ui/badge";
import { StatusBadge } from "@/components/status-badge";
import { STATUS_LABELS, statusTone } from "@/lib/constants";

describe("Badge", () => {
  it("renders children with a tone class", () => {
    const { container } = render(<Badge tone="teal">Active</Badge>);
    expect(screen.getByText("Active")).toBeInTheDocument();
    expect(container.querySelector("span")?.className).toContain("bg-brand-50");
  });
});

describe("StatusBadge", () => {
  it("maps statuses to friendly labels", () => {
    expect(STATUS_LABELS["ACTIVE"]).toBe("Active");
    render(<StatusBadge value="COMPLETED" />);
    expect(screen.getByText("Completed")).toBeInTheDocument();
  });

  it("assigns a non-neutral tone for high visibility states", () => {
    expect(statusTone("URGENT")).toBe("amber");
    expect(statusTone("CANCELLED")).toBe("rose");
    expect(statusTone("COMPLETED")).toBe("emerald");
    expect(statusTone("DRAFT")).toBe("neutral");
  });
});