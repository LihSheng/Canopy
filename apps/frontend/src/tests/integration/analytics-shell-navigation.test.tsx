import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

let mockPathname = "/dashboard";

vi.mock("@/hooks/use-session", () => ({
  useSession: () => ({
    user: { id: "1", email: "test@test.com", display_name: "Test User", role: "admin" },
    loading: false,
    error: null,
    refetch: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("@/components/auth/session-guard", () => ({
  useTenant: () => ({
    tenant: { tenant_id: "tenant-1", role: "admin" },
    tenants: [
      { tenant_id: "tenant-1", name: "Alpha Corp", role: "admin" },
      { tenant_id: "tenant-2", name: "Beta Inc", role: "member" },
    ],
    refetch: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => mockPathname,
  useSearchParams: () => new URLSearchParams(),
}));

import { AnalyticsShell } from "@/components/analytics-shell/analytics-shell";
import { AnalyticsLayoutProvider } from "@/components/analytics-shell/analytics-layout-context";

const Wrapper = ({ children }: { children: React.ReactNode }) => {
  return <AnalyticsLayoutProvider>{children}</AnalyticsLayoutProvider>;
}

describe("Analytics shell navigation stability", () => {
  beforeEach(() => {
    mockPathname = "/dashboard";
    vi.clearAllMocks();
  });

  it("renders sidebar shell on dashboard page", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div data-testid="dashboard-content">Dashboard Content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Anomalies")).toBeInTheDocument();
    expect(screen.getByText("Departments")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();
    expect(screen.getByTestId("dashboard-content")).toBeInTheDocument();
  });

  it("keeps sidebar visible on anomalies page", () => {
    mockPathname = "/dashboard/anomalies";

    render(
      <Wrapper>
        <AnalyticsShell>
          <div data-testid="anomalies-content">Anomalies Content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Anomalies")).toBeInTheDocument();
    expect(screen.getByTestId("anomalies-content")).toBeInTheDocument();
  });

  it("keeps sidebar visible on departments page", () => {
    mockPathname = "/dashboard/departments";

    render(
      <Wrapper>
        <AnalyticsShell>
          <div data-testid="departments-content">Departments Content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Departments")).toBeInTheDocument();
    expect(screen.getByTestId("departments-content")).toBeInTheDocument();
  });

  it("keeps sidebar visible on reports page", () => {
    mockPathname = "/dashboard/reports";

    render(
      <Wrapper>
        <AnalyticsShell>
          <div data-testid="reports-content">Reports Content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();
    expect(screen.getByTestId("reports-content")).toBeInTheDocument();
  });

  it("keeps sidebar visible on profile page", () => {
    mockPathname = "/dashboard/profile";

    render(
      <Wrapper>
        <AnalyticsShell>
          <div data-testid="profile-content">Profile Content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("profile-content")).toBeInTheDocument();
  });

  it("maintains shell structure when navigating (re-rendering with different pathname)", () => {
    mockPathname = "/dashboard";

    const { rerender } = render(
      <Wrapper>
        <AnalyticsShell>
          <div data-testid="content">Dashboard Content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByTestId("content")).toBeInTheDocument();

    mockPathname = "/dashboard/anomalies";

    rerender(
      <Wrapper>
        <AnalyticsShell>
          <div data-testid="content">Anomalies Content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    // Sidebar items are still present
    expect(screen.getByText("Dashboard")).toBeInTheDocument();
    expect(screen.getByText("Anomalies")).toBeInTheDocument();
    expect(screen.getByText("Departments")).toBeInTheDocument();
    expect(screen.getByText("Reports")).toBeInTheDocument();

    // Content updated
    expect(screen.getByTestId("content")).toHaveTextContent("Anomalies Content");
  });

  it("renders utility zone with profile and logout", () => {
    render(
      <Wrapper>
        <AnalyticsShell>
          <div>Page content</div>
        </AnalyticsShell>
      </Wrapper>
    );

    expect(screen.getByText("Profile")).toBeInTheDocument();
    expect(screen.getByText("Test User")).toBeInTheDocument();
  });
});
