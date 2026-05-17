import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

const mockPush = vi.fn();

vi.mock("@/hooks/use-session", () => ({
  useSession: () => ({
    user: { id: "1", email: "test@test.com", display_name: "Test User" },
    loading: false, error: null, refetch: vi.fn(), logout: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush, replace: vi.fn() }),
  usePathname: () => "/dashboard/departments/d1",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/api/client", () => ({
  request: vi.fn(),
}));

vi.mock("@/lib/api/dashboard", () => ({
  fetchDepartmentDetail: vi.fn(),
  fetchEmployeeContributions: vi.fn(),
  fetchClaimDetails: vi.fn(),
  fetchAnomalies: vi.fn(),
  fetchSummary: vi.fn(),
  fetchDepartments: vi.fn(),
  fetchMonthlyTrends: vi.fn(),
  fetchClaimTypeBreakdown: vi.fn(),
  fetchRefreshStatus: vi.fn().mockResolvedValue({
    status: "idle", last_refresh: "2024-06-01T00:00:00Z", last_attempt: null, error_message: null,
  }),
  triggerRefresh: vi.fn(),
}));

import { DepartmentDetailPage } from "@/components/department-detail/department-detail-page";
import * as api from "@/lib/api/dashboard";
import * as client from "@/lib/api/client";

const mockDept = {
  id: "d1", name: "Engineering", payroll_spend: 400_000, claims_spend: 100_000,
  total_spend: 500_000, change_pct: 5.0, employee_count: 42,
};

const mockEmployees = [
  { id: "e1", name: "Alice", department: "Engineering", payroll: 120_000, claims: 10_000, total: 130_000 },
  { id: "e2", name: "Bob", department: "Engineering", payroll: 110_000, claims: 5_000, total: 115_000 },
  { id: "e3", name: "Carol", department: "Engineering", payroll: 100_000, claims: 30_000, total: 130_000 },
  { id: "e4", name: "Dave", department: "Engineering", payroll: 50_000, claims: 2_000, total: 52_000 },
  { id: "e5", name: "Eve", department: "Engineering", payroll: 60_000, claims: 1_000, total: 61_000 },
];

const mockClaims = [
  { id: "c1", employee_name: "Alice", department: "Engineering", type: "Medical", amount: 5_000, date: "2024-06-01" },
  { id: "c2", employee_name: "Carol", department: "Engineering", type: "Medical", amount: 20_000, date: "2024-06-05" },
  { id: "c3", employee_name: "Bob", department: "Engineering", type: "Dental", amount: 5_000, date: "2024-06-10" },
  { id: "c4", employee_name: "Alice", department: "Engineering", type: "Vision", amount: 5_000, date: "2024-06-12" },
  { id: "c5", employee_name: "Carol", department: "Engineering", type: "Pharmacy", amount: 10_000, date: "2024-06-15" },
];

const mockAnomalies = [
  { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike", severity: "high" as const, change_pct: 15 },
];

const mockTrends = [
  { month: "2024-01", payroll: 380_000, claims: 90_000, total: 470_000 },
  { month: "2024-02", payroll: 390_000, claims: 95_000, total: 485_000 },
  { month: "2024-03", payroll: 400_000, claims: 100_000, total: 500_000 },
];

describe("Department Detail V2 integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchDepartmentDetail).mockResolvedValue(mockDept);
    vi.mocked(api.fetchEmployeeContributions).mockResolvedValue(mockEmployees);
    vi.mocked(api.fetchClaimDetails).mockResolvedValue(mockClaims);
    vi.mocked(api.fetchAnomalies).mockResolvedValue(mockAnomalies);
    vi.mocked(client.request).mockResolvedValue(mockTrends);
    mockPush.mockClear();
  });

  it("loads and renders breadcrumb and department name", async () => {
    render(<DepartmentDetailPage id="d1" />);

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });
    expect(screen.getByText("Departments")).toBeInTheDocument();
  });

  it("renders department detail header with name, spend, and change", async () => {
    render(<DepartmentDetailPage id="d1" />);

    await waitFor(() => {
      expect(screen.getAllByText("Engineering").length).toBeGreaterThanOrEqual(1);
    });
    expect(screen.getByText("$500,000")).toBeInTheDocument();
    expect(screen.getByText("+5.0%")).toBeInTheDocument();
  });

  it("renders attention badge for flagged department", async () => {
    render(<DepartmentDetailPage id="d1" />);

    await waitFor(() => {
      expect(screen.getByText("high")).toBeInTheDocument();
    });
  });

  it("renders AI summary", async () => {
    render(<DepartmentDetailPage id="d1" />);

    await waitFor(() => {
      expect(screen.getByText("AI")).toBeInTheDocument();
    });
  });

  it("renders contributor panels side-by-side", async () => {
    render(<DepartmentDetailPage id="d1" />);

    await waitFor(() => {
      expect(screen.getByText("Top Employees")).toBeInTheDocument();
    });
    expect(screen.getByText("Top Claim Types")).toBeInTheDocument();
  });

  it("refetches all data on time range change", async () => {
    render(<DepartmentDetailPage id="d1" />);

    await waitFor(() => {
      expect(screen.getAllByText("Engineering").length).toBeGreaterThanOrEqual(1);
    });

    const fetchDeptCalls = vi.mocked(api.fetchDepartmentDetail).mock.calls.length;
    const fetchEmplCalls = vi.mocked(api.fetchEmployeeContributions).mock.calls.length;
    const fetchClaimsCalls = vi.mocked(api.fetchClaimDetails).mock.calls.length;

    fireEvent.click(screen.getByText("Last 3 months"));

    await waitFor(() => {
      expect(vi.mocked(api.fetchDepartmentDetail).mock.calls.length).toBeGreaterThan(fetchDeptCalls);
    });
    expect(vi.mocked(api.fetchEmployeeContributions).mock.calls.length).toBeGreaterThan(fetchEmplCalls);
    expect(vi.mocked(api.fetchClaimDetails).mock.calls.length).toBeGreaterThan(fetchClaimsCalls);
  });

  it("renders View related anomalies CTA with correct link", async () => {
    render(<DepartmentDetailPage id="d1" />);

    await waitFor(() => {
      expect(screen.getByText("View related anomalies")).toBeInTheDocument();
    });

    const ctaLink = screen.getByText("View related anomalies").closest("a");
    expect(ctaLink).toHaveAttribute("href");
    expect(ctaLink!.getAttribute("href")).toContain("/dashboard/anomalies");
    expect(ctaLink!.getAttribute("href")).toContain("department_id=d1");
  });

  it("shows error state when API fails", async () => {
    vi.mocked(api.fetchDepartmentDetail).mockRejectedValue(new Error("Network error"));

    render(<DepartmentDetailPage id="d1" />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
    expect(screen.getByText("Try again")).toBeInTheDocument();
  });

  it("shows loading state initially", () => {
    render(<DepartmentDetailPage id="d1" />);

    expect(screen.getAllByText("Loading...").length).toBeGreaterThanOrEqual(1);
  });
});
