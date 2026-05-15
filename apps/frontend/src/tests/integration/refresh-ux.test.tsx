import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("@/hooks/use-session", () => ({
  useSession: () => ({ user: { id: "1", email: "test@test.com", display_name: "Test" }, loading: false, error: null, refetch: vi.fn(), logout: vi.fn() }),
}));

vi.mock("@/lib/api/dashboard", () => ({
  fetchSummary: vi.fn(),
  fetchDepartments: vi.fn(),
  fetchMonthlyTrends: vi.fn(),
  fetchClaimTypeBreakdown: vi.fn(),
  fetchAnomalies: vi.fn(),
  fetchRefreshStatus: vi.fn().mockResolvedValue({ status: "idle", last_refresh: "2024-06-01T00:00:00Z", last_attempt: null, error_message: null }),
  triggerRefresh: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));

import { DashboardNav } from "@/components/dashboard/nav-bar";
import { RefreshStatusBadge, RefreshTimelinePanel } from "@/components/dashboard/refresh-widgets";
import * as api from "@/lib/api/dashboard";

describe("Refresh UX", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders refresh badge in nav bar", async () => {
    const mockStatus = { status: "idle" as const, last_refresh: "2024-06-01T00:00:00Z", last_attempt: null, error_message: null };
    vi.mocked(api.fetchRefreshStatus).mockResolvedValue(mockStatus);

    render(<DashboardNav />);

    await waitFor(() => {
      expect(screen.getByText("Up to date")).toBeInTheDocument();
    });
  });

  it("shows running badge when refresh is active", async () => {
    const mockStatus = { status: "running" as const, last_refresh: null, last_attempt: null, error_message: null };
    vi.mocked(api.fetchRefreshStatus).mockResolvedValue(mockStatus);

    render(<DashboardNav />);

    await waitFor(() => {
      expect(screen.getByText("Refreshing...")).toBeInTheDocument();
    });
  });

  it("renders refresh timeline panel with refresh dates", () => {
    render(
      <RefreshTimelinePanel
        lastRefresh="2024-06-15T10:30:00Z"
        lastAttempt={null}
      />,
    );
    expect(screen.getByText(/Last refresh:/)).toBeInTheDocument();
    expect(screen.getByText(/Jun 15/)).toBeInTheDocument();
  });

  it("shows last attempt when it differs from last refresh", () => {
    render(
      <RefreshTimelinePanel
        lastRefresh="2024-06-15T10:30:00Z"
        lastAttempt="2024-06-15T11:00:00Z"
      />,
    );
    expect(screen.getByText(/Last attempt:/)).toBeInTheDocument();
  });
});
