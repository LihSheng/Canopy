import { render, screen, waitFor, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi, beforeEach } from "vitest";

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
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard/anomalies",
  useSearchParams: () => new URLSearchParams(),
}));

vi.mock("@/lib/api/dashboard", () => ({
  fetchAnomalies: vi.fn(),
  fetchSummary: vi.fn(),
  fetchDepartments: vi.fn(),
  fetchMonthlyTrends: vi.fn(),
  fetchClaimTypeBreakdown: vi.fn(),
  fetchRefreshStatus: vi.fn().mockResolvedValue({
    status: "idle",
    last_refresh: "2024-06-01T00:00:00Z",
    last_attempt: null,
    error_message: null,
  }),
  triggerRefresh: vi.fn(),
}));

import { AnomaliesPage } from "@/components/anomalies-v2/anomalies-page";
import * as api from "@/lib/api/dashboard";

const mockAnomalies = [
  { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike", severity: "high" as const, change_pct: 15 },
  { id: "a2", department_id: "d3", department_name: "Marketing", period: "2024-06", description: "Unusual claims", severity: "high" as const, change_pct: 12 },
  { id: "a3", department_id: "d2", department_name: "Sales", period: "2024-06", description: "Moderate increase", severity: "medium" as const, change_pct: 8 },
  { id: "a4", department_id: "d4", department_name: "HR", period: "2024-06", description: "Small uptick", severity: "low" as const, change_pct: 3 },
];

describe("Anomalies V2 integration", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(api.fetchAnomalies).mockResolvedValue(mockAnomalies);
  });

  it("loads and renders breadcrumb and header", async () => {
    render(<AnomaliesPage />);

    await waitFor(() => {
      expect(screen.getByText("Dashboard")).toBeInTheDocument();
    });

    const anomaliesElements = screen.getAllByText("Anomalies");
    expect(anomaliesElements.length).toBeGreaterThanOrEqual(1);
  });

  it("renders severity-grouped anomaly rows", async () => {
    render(<AnomaliesPage />);

    await waitFor(() => {
      expect(screen.getByText("High severity")).toBeInTheDocument();
    });

    expect(screen.getByText("Medium severity")).toBeInTheDocument();
    expect(screen.getByText("Low severity")).toBeInTheDocument();
  });

  it("expands high group by default", async () => {
    render(<AnomaliesPage />);

    await waitFor(() => {
      expect(screen.getByText("Engineering")).toBeInTheDocument();
      expect(screen.getByText("Marketing")).toBeInTheDocument();
    });
  });

  it("collapses medium and low groups by default", async () => {
    render(<AnomaliesPage />);

    await waitFor(() => {
      expect(screen.getByText("Medium severity")).toBeInTheDocument();
    });

    expect(screen.queryByText("Sales")).not.toBeInTheDocument();
  });

  it("toggles group on click", async () => {
    render(<AnomaliesPage />);

    await waitFor(() => {
      expect(screen.getByText("Medium severity")).toBeInTheDocument();
    });

    const mediumButton = screen.getByText("Medium severity").closest("button");
    expect(mediumButton).toBeInTheDocument();

    if (mediumButton) fireEvent.click(mediumButton);

    await waitFor(() => {
      expect(screen.getByText("Sales")).toBeInTheDocument();
    });
  });

  it("has anomaly rows linking to department detail", async () => {
    render(<AnomaliesPage />);

    await waitFor(() => {
      expect(screen.getByText("Engineering")).toBeInTheDocument();
    });

    const links = screen.getAllByRole("link");
    const engLink = links.find(
      (l) =>
        l.getAttribute("href")?.includes("departments/d1") &&
        l.getAttribute("href")?.includes("source=anomalies") &&
        l.getAttribute("href")?.includes("anomaly_id=a1"),
    );
    expect(engLink).toBeDefined();
  });

  it("shows error state when API fails", async () => {
    vi.mocked(api.fetchAnomalies).mockRejectedValue(new Error("Network error"));

    render(<AnomaliesPage />);

    await waitFor(() => {
      expect(screen.getByText("Network error")).toBeInTheDocument();
    });
  });

  it("shows severity filter bar", async () => {
    render(<AnomaliesPage />);

    await waitFor(() => {
      expect(screen.getByText("All")).toBeInTheDocument();
    });

    expect(screen.getByText("Range:")).toBeInTheDocument();
    expect(screen.getByText("Severity:")).toBeInTheDocument();
  });
});
