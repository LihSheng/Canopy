import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("@/hooks/use-session", () => ({
  useSession: () => ({ user: { id: "1", email: "test@test.com", display_name: "Test" }, loading: false, error: null, refetch: vi.fn(), logout: vi.fn() }),
}));

vi.mock("@/lib/api/dashboard", () => ({
  fetchCommandView: vi.fn(),
  fetchRefreshStatus: vi.fn().mockResolvedValue({ status: "idle", last_refresh: "2024-06-01T00:00:00Z", last_attempt: null, error_message: null }),
  triggerRefresh: vi.fn(),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));

import { DashboardPage } from "@/components/dashboard/dashboard-page";
import * as api from "@/lib/api/dashboard";

const mockCommandView = {
  summary: {
    total_payroll: 1000000,
    total_claims: 200000,
    period: { year: 2024, month: 6 },
    department_count: 5,
    anomaly_count: 2,
    last_updated: "2024-06-15T10:00:00Z",
  },
  departments: [
    { id: "d1", name: "Engineering", total_spend: 500000, payroll_spend: 400000, claims_spend: 100000, change_pct: 5.0 },
    { id: "d2", name: "Sales", total_spend: 300000, payroll_spend: 200000, claims_spend: 100000, change_pct: -2.0 },
  ],
  trends: [
    { month: "2024-01", payroll: 900000, claims: 180000, total: 1080000 },
    { month: "2024-02", payroll: 950000, claims: 190000, total: 1140000 },
  ],
  claim_types: [
    { type: "Travel", amount: 100000, count: 50 },
    { type: "Meals", amount: 50000, count: 30 },
  ],
  anomalies: [
    { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike", severity: "high" as const, change_pct: 15 },
  ],
};

const mockSummary = {
  total_payroll: 1000000,
  total_claims: 200000,
  period: { year: 2024, month: 6 },
  department_count: 5,
  anomaly_count: 2,
  last_updated: "2024-06-15T10:00:00Z",
};

const mockDepartments = [
  { id: "d1", name: "Engineering", total_spend: 500000, payroll_spend: 400000, claims_spend: 100000, change_pct: 5.0 },
  { id: "d2", name: "Sales", total_spend: 300000, payroll_spend: 200000, claims_spend: 100000, change_pct: -2.0 },
];

const mockTrends = [
  { month: "Jan", payroll: 900000, claims: 180000, total: 1080000 },
  { month: "Feb", payroll: 950000, claims: 190000, total: 1140000 },
];

const mockClaimTypes = [
  { type: "Travel", amount: 100000, count: 50 },
  { type: "Meals", amount: 50000, count: 30 },
];

const mockAnomalies = [
  { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike", severity: "high" as const, change_pct: 15 },
];

describe("Dashboard flow", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("loads and displays the dashboard command view", async () => {
    vi.mocked(api.fetchCommandView).mockResolvedValue(mockCommandView);

    render(<DashboardPage />);

    // DashboardPage renders "Dashboard" as the page title
    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });

    await waitFor(() => {
      // Payroll spend card shows $1,000,000
      expect(screen.getByText("$1,000,000")).toBeInTheDocument();
      // Claims spend card shows $200,000
      expect(screen.getByText("$200,000")).toBeInTheDocument();
    });
  });

  it("shows error state when API fails", async () => {
    vi.mocked(api.fetchCommandView).mockRejectedValue(new Error("Network error"));

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    const retryBtn = screen.getByText("Try again");
    expect(retryBtn).toBeInTheDocument();
  });

  it("shows anomaly card with data", async () => {
    vi.mocked(api.fetchCommandView).mockResolvedValue(mockCommandView);

    render(<DashboardPage />);

    await waitFor(() => {
      const engineeringElements = screen.getAllByText("Engineering");
      expect(engineeringElements.length).toBeGreaterThanOrEqual(1);
    });

    await waitFor(() => {
      expect(screen.getByText("Payroll spike")).toBeInTheDocument();
    });
  });
});
