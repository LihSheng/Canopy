import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/hooks/use-session", () => ({
  useSession: () => ({
    user: { id: "u-001", email: "alice@example.com", display_name: "Alice Tan" },
    loading: false,
    error: null,
    refetch: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard/profile",
  useSearchParams: () => new URLSearchParams(),
}));

import { ProfilePage } from "@/components/profile-v2/profile-page";

describe("Profile V2 integration", () => {
  it("renders full profile page with breadcrumb trail", () => {
    render(<ProfilePage />);

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Profile" })).toBeInTheDocument();
  });

  it("displays user identity summary", () => {
    render(<ProfilePage />);

    expect(screen.getByRole("heading", { name: "Alice Tan" })).toBeInTheDocument();
    expect(screen.getByText("u-001")).toBeInTheDocument();
  });

  it("has the email in the header context area", () => {
    render(<ProfilePage />);

    const emailMatches = screen.getAllByText("alice@example.com");
    expect(emailMatches.length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("User ID")).toBeInTheDocument();
    expect(screen.getByText("Display name")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
  });
});
