import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const mockRouterPush = vi.fn();

vi.mock("@/hooks/use-session", () => ({
  useSession: () => ({
    user: { id: "1", email: "test@test.com", display_name: "Test User" },
    loading: false,
    error: null,
    refetch: vi.fn(),
    logout: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockRouterPush, replace: vi.fn() }),
  usePathname: () => "/dashboard",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/api/dashboard", () => ({
  fetchSummary: vi.fn(),
  fetchDepartments: vi.fn(),
  fetchMonthlyTrends: vi.fn(),
  fetchClaimTypeBreakdown: vi.fn(),
  fetchAnomalies: vi.fn(),
  fetchRefreshStatus: vi.fn().mockResolvedValue({
    status: "idle",
    last_refresh: "2024-06-01T00:00:00Z",
    last_attempt: null,
    error_message: null,
  }),
  triggerRefresh: vi.fn(),
}));

import { DashboardPage } from "@/components/dashboard-v2/dashboard-page";
import * as api from "@/lib/api/dashboard";

const mockSummary = {
  total_payroll: 1_000_000,
  total_claims: 200_000,
  period: { year: 2024, month: 6 },
  department_count: 5,
  anomaly_count: 2,
  last_updated: "2024-06-15T10:00:00Z",
};

const mockDepartments = [
  { id: "d1", name: "Engineering", total_spend: 500_000, payroll_spend: 400_000, claims_spend: 100_000, change_pct: 5.0 },
  { id: "d2", name: "Sales", total_spend: 300_000, payroll_spend: 200_000, claims_spend: 100_000, change_pct: -2.0 },
  { id: "d3", name: "Marketing", total_spend: 200_000, payroll_spend: 150_000, claims_spend: 50_000, change_pct: 12.0 },
  { id: "d4", name: "HR", total_spend: 150_000, payroll_spend: 120_000, claims_spend: 30_000, change_pct: 0.0 },
  { id: "d5", name: "Finance", total_spend: 120_000, payroll_spend: 100_000, claims_spend: 20_000, change_pct: -8.0 },
];

const mockTrends = [
  { month: "2024-01", payroll: 900_000, claims: 180_000, total: 1_080_000 },
  { month: "2024-02", payroll: 950_000, claims: 190_000, total: 1_140_000 },
  { month: "2024-03", payroll: 1_000_000, claims: 200_000, total: 1_200_000 },
];

const mockClaimTypes = [
  { type: "Travel", amount: 100_000, count: 50 },
  { type: "Meals", amount: 50_000, count: 30 },
];

const mockAnomalies = [
  { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike", severity: "high" as const, change_pct: 15 },
  { id: "a2", department_id: "d3", department_name: "Marketing", period: "2024-06", description: "Unusual claims", severity: "medium" as const, change_pct: 12 },
];

describe("Dashboard V2 integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockRouterPush.mockClear();
    vi.mocked(api.fetchSummary).mockResolvedValue(mockSummary);
    vi.mocked(api.fetchDepartments).mockResolvedValue(mockDepartments);
    vi.mocked(api.fetchMonthlyTrends).mockResolvedValue(mockTrends);
    vi.mocked(api.fetchClaimTypeBreakdown).mockResolvedValue(mockClaimTypes);
    vi.mocked(api.fetchAnomalies).mockResolvedValue(mockAnomalies);
  });

  it("loads and renders dashboard command view", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText("Top Attention Items")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText("Top Departments")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText("AI Summary")).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText("Monthly Trends")).toBeInTheDocument();
    });
  });

  it("renders attention items with department names", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      const engineeringElements = screen.getAllByText("Engineering");
      expect(engineeringElements.length).toBeGreaterThanOrEqual(1);
    });

    await waitFor(() => {
      expect(screen.getByText("Payroll spike")).toBeInTheDocument();
    });
  });

  it("renders summary card values", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("$1,200,000")).toBeInTheDocument();
      expect(screen.getByText("$1,000,000")).toBeInTheDocument();
      const claimsElements = screen.getAllByText("$200,000");
      expect(claimsElements.length).toBeGreaterThanOrEqual(1);
    });
  });

  it("has attention count card linking to anomalies", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      const attentionLinks = screen.getAllByRole("link");
      const anomaliesLink = attentionLinks.find(
        (link) => link.getAttribute("href") === "/dashboard/anomalies"
      );
      expect(anomaliesLink).toBeDefined();
    });
  });

  it("has top attention item linking to department detail", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      const links = screen.getAllByRole("link");
      const detailLink = links.find(
        (link) =>
          link.getAttribute("href")?.includes("departments/d1") &&
          link.getAttribute("href")?.includes("source=dashboard_attention")
      );
      expect(detailLink).toBeDefined();
    });
  });

  it("has department preview row linking to detail", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      const links = screen.getAllByRole("link");
      const deptLink = links.find(
        (link) =>
          link.getAttribute("href")?.includes("departments/d1") &&
          link.getAttribute("href")?.includes("source=dashboard_ranking")
      );
      expect(deptLink).toBeDefined();
    });
  });

  it("renders View all anomalies CTA", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("View all anomalies →")).toBeInTheDocument();
    });
  });

  it("renders View all departments CTA", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("View all departments →")).toBeInTheDocument();
    });
  });

  it("shows error state when API fails", async () => {
    vi.mocked(api.fetchSummary).mockRejectedValue(new Error("Network error"));

    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });

    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("shows AI summary with headline and bullets", async () => {
    render(<DashboardPage />);

    await waitFor(() => {
      expect(screen.getByText("Spend overview for 2024-06")).toBeInTheDocument();
    });
  });
});
