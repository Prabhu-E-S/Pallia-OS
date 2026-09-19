import { describe, expect, it } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/feedback";

describe("Button", () => {
  it("renders with default primary styling and click handler", () => {
    let clicked = false;
    render(<Button onClick={() => (clicked = true)}>Save</Button>);
    const button = screen.getByRole("button", { name: "Save" });
    expect(button).toBeInTheDocument();
    fireEvent.click(button);
    expect(clicked).toBe(true);
  });

  it("is disabled when requested", () => {
    render(
      <Button disabled onClick={() => undefined}>
        Send
      </Button>,
    );
    expect(screen.getByRole("button", { name: "Send" })).toBeDisabled();
  });
});

describe("EmptyState", () => {
  it("shows title and description", () => {
    render(<EmptyState title="No tasks" description="Create a task to get started." />);
    expect(screen.getByText("No tasks")).toBeInTheDocument();
    expect(screen.getByText("Create a task to get started.")).toBeInTheDocument();
  });
});