import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { LoginForm } from "@/components/auth/login-form";

describe("LoginForm", () => {
  it("renders email and password inputs", () => {
    render(<LoginForm onSubmit={vi.fn()} error={null} loading={false} />);

    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Password")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
  });

  it("calls onSubmit with email and password", async () => {
    const onSubmit = vi.fn().mockResolvedValue(undefined);
    render(<LoginForm onSubmit={onSubmit} error={null} loading={false} />);

    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "test@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "secret" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => {
      expect(onSubmit).toHaveBeenCalledWith("test@example.com", "secret");
    });
  });

  it("disables button when loading", () => {
    render(<LoginForm onSubmit={vi.fn()} error={null} loading={true} />);

    const button = screen.getByRole("button", { name: "Signing in..." });
    expect(button).toBeDisabled();
  });

  it("shows error message when provided", () => {
    render(
      <LoginForm
        onSubmit={vi.fn()}
        error="Invalid credentials"
        loading={false}
      />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("Invalid credentials");
  });

  it("does not show error when null", () => {
    render(<LoginForm onSubmit={vi.fn()} error={null} loading={false} />);

    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });
});
