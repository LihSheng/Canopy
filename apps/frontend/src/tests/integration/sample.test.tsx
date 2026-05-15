import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

describe("sample integration", () => {
  it("renders simple element", () => {
    render(<div data-testid="hello">Hello</div>);
    expect(screen.getByTestId("hello")).toHaveTextContent("Hello");
  });
});
