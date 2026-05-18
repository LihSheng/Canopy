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

import { ProfilePage } from "@/components/profile/profile-page";
import { ProfileIdentityCard, ProfileIdentityCardSkeleton } from "@/components/profile/profile-identity-card";
import type { SessionUser } from "@/lib/api/auth";

const mockUser: SessionUser = { id: "u-001", email: "alice@example.com", display_name: "Alice Tan" };

describe("ProfileIdentityCard", () => {
  it("renders user display name, email, and id", () => {
    render(<ProfileIdentityCard user={mockUser} />);

    expect(screen.getByRole("heading", { name: "Alice Tan" })).toBeInTheDocument();
    expect(screen.getAllByText("alice@example.com").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("u-001")).toBeInTheDocument();
  });

  it("renders field labels", () => {
    render(<ProfileIdentityCard user={mockUser} />);

    expect(screen.getByText("User ID")).toBeInTheDocument();
    expect(screen.getByText("Display name")).toBeInTheDocument();
    expect(screen.getByText("Email")).toBeInTheDocument();
  });
});

describe("ProfileIdentityCardSkeleton", () => {
  it("renders the skeleton container", () => {
    const { container } = render(<ProfileIdentityCardSkeleton />);

    const skeleton = container.querySelector(".animate-pulse");
    expect(skeleton).toBeInTheDocument();
  });
});

describe("ProfilePage", () => {
  it("renders header, breadcrumb, and identity card", () => {
    render(<ProfilePage />);

    expect(screen.getByRole("heading", { name: "Profile" })).toBeInTheDocument();
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Alice Tan" })).toBeInTheDocument();
  });

  it("shows email as header context text", () => {
    render(<ProfilePage />);

    const contextElements = screen.getAllByText("alice@example.com");
    expect(contextElements.length).toBeGreaterThanOrEqual(1);
  });
});
