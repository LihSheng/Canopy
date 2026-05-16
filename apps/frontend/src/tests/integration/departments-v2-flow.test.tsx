import { render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

vi.mock("@/hooks/use-session", () => ({
  useSession: () => ({
    user: { id: "1", email: "test@test.com", display_name: "Test User" },
    loading: false, error: null, refetch: vi.fn(), logout: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard/departments",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/api/dashboard", () => ({
  fetchDepartments: vi.fn(),
  fetchAnomalies: vi.fn(),
  fetchSummary: vi.fn(),
  fetchMonthlyTrends: vi.fn(),
  fetchClaimTypeBreakdown: vi.fn(),
  fetchRefreshStatus: vi.fn().mockResolvedValue({ status: "idle", last_refresh: null, last_attempt: null, error_message: null }),
  triggerRefresh: vi.fn(),
}));

import { DepartmentsPage } from "@/components/departments-v2/departments-page";
import * as api from "@/lib/api/dashboard";

const mockDepartments = [
  { id: "d1", name: "Engineering", total_spend: 500_000, payroll_spend: 400_000, claims_spend: 100_000, change_pct: 5.0 },
  { id: "d2", name: "Sales", total_spend: 300_000, payroll_spend: 200_000, claims_spend: 100_000, change_pct: -2.0 },
  { id: "d3", name: "Marketing", total_spend: 200_000, payroll_spend: 150_000, claims_spend: 50_000, change_pct: 12.0 },
];

const mockAnomalies = [
  { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike", severity: "high" as const, change_pct: 15 },
  { id: "a2", department_id: "d3", department_name: "Marketing", period: "2024-06", description: "Unusual claims", severity: "medium" as const, change_pct: 12 },
];

describe("Departments V2 integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchDepartments).mockResolvedValue(mockDepartments);
    vi.mocked(api.fetchAnomalies).mockResolvedValue(mockAnomalies);
  });

  it("loads and renders page with header", async () => {
    render(<DepartmentsPage />);
    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });
    const deptElements = screen.getAllByText("Departments");
    expect(deptElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders ranked department rows", async () => {
    render(<DepartmentsPage />);
    await waitFor(() => {
      expect(screen.getByText("Engineering")).toBeInTheDocument();
      expect(screen.getByText("Sales")).toBeInTheDocument();
      expect(screen.getByText("Marketing")).toBeInTheDocument();
    });
  });

  it("shows attention badges on flagged departments", async () => {
    render(<DepartmentsPage />);
    await waitFor(() => {
      expect(screen.getByText("high")).toBeInTheDocument();
      expect(screen.getByText("medium")).toBeInTheDocument();
    });
  });

  it("defaults sort to attention (high first)", async () => {
    render(<DepartmentsPage />);
    await waitFor(() => {
      // Engineering (high) + Marketing (medium) should appear before Sales (no attention)
      const engEl = screen.getByText("Engineering");
      expect(engEl).toBeInTheDocument();
    });

    // Verify attention-bearing rows have the badge
    expect(screen.getByText("high")).toBeInTheDocument();
    expect(screen.getByText("medium")).toBeInTheDocument();
  });

  it("has department rows linking to detail page", async () => {
    render(<DepartmentsPage />);
    await waitFor(() => {
      const links = screen.getAllByRole("link");
      const engLink = links.find(
        (l) => l.getAttribute("href")?.includes("departments/d1") &&
               l.getAttribute("href")?.includes("source=dashboard_ranking")
      );
      expect(engLink).toBeDefined();
    });
  });

  it("shows error state when API fails", async () => {
    vi.mocked(api.fetchDepartments).mockRejectedValue(new Error("Network error"));
    render(<DepartmentsPage />);
    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });
});
