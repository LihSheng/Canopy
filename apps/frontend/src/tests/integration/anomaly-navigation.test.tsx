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
  fetchDepartmentDetail: vi.fn(),
  fetchEmployeeContributions: vi.fn(),
  fetchClaimDetails: vi.fn(),
  fetchRefreshStatus: vi.fn().mockResolvedValue({ status: "idle", last_refresh: null, last_attempt: null, error_message: null }),
  triggerRefresh: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard/anomalies",
  useSearchParams: () => new URLSearchParams(),
}));

import { AnomaliesPage } from "@/components/anomalies/anomalies-page";
import * as api from "@/lib/api/dashboard";

describe("Anomaly navigation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("displays anomaly list", async () => {
    vi.mocked(api.fetchAnomalies).mockResolvedValue([
      { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike of 15%", severity: "high" as const, change_pct: 15 },
      { id: "a2", department_id: "d2", department_name: "Sales", period: "2024-05", description: "Claims drop", severity: "low" as const, change_pct: -8 },
    ]);

    render(<AnomaliesPage />);

    await waitFor(() => {
      // High-severity group is expanded by default, so its items are visible
      expect(screen.getByText("Payroll spike of 15%")).toBeInTheDocument();
      // Low-severity group is collapsed by default
      expect(screen.queryByText("Claims drop")).not.toBeInTheDocument();
    });
  });

  it("shows empty state when no anomalies", async () => {
    vi.mocked(api.fetchAnomalies).mockResolvedValue([]);

    render(<AnomaliesPage />);

    await waitFor(() => {
      expect(screen.getByText("No anomalies detected")).toBeInTheDocument();
    });
  });

  it("shows error state on API failure", async () => {
    vi.mocked(api.fetchAnomalies).mockRejectedValue(new Error("Server error"));

    render(<AnomaliesPage />);

    await waitFor(() => {
      expect(screen.getByText("Server error")).toBeInTheDocument();
    });
  });
});
