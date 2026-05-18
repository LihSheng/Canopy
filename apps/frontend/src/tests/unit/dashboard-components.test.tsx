import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

const mockPush = vi.fn();

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
  useRouter: () => ({ push: mockPush, replace: vi.fn() }),
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

import { DashboardSummaryGrid, DashboardSummaryGridSkeleton } from "@/components/dashboard/dashboard-summary-grid";
import { DashboardAttentionPanel } from "@/components/dashboard/dashboard-attention-panel";
import { DashboardAttentionItem } from "@/components/dashboard/dashboard-attention-item";
import { DashboardAiSummaryPanel } from "@/components/dashboard/dashboard-ai-summary-panel";
import { DashboardDepartmentPreview } from "@/components/dashboard/dashboard-department-preview";
import type { AttentionListItem, DepartmentPreviewItem, SummaryBrief } from "@/components/dashboard/dashboard-mappers";

const mockCards = {
  totalSpend: { label: "Total Spend", value: 1_200_000, clickable: false },
  payrollSpend: { label: "Payroll Spend", value: 1_000_000, clickable: false },
  claimsSpend: { label: "Claims Spend", value: 200_000, clickable: false },
  attentionCount: { label: "Attention Count", value: 2, clickable: true },
};

const mockAttentionItems: AttentionListItem[] = [
  {
    id: "a1",
    departmentId: "d1",
    departmentName: "Engineering",
    severity: "high",
    reason: "Payroll spike",
    changePct: 15,
  },
  {
    id: "a2",
    departmentId: "d3",
    departmentName: "Marketing",
    severity: "medium",
    reason: "Unusual claims",
    changePct: 12,
  },
];

const mockAiSummary: SummaryBrief = {
  headline: "Spend overview for 2024-06",
  bullets: ["Total spend: $1200k", "2 anomalies detected", "Top claim: Travel"],
};

const mockDeptPreview: DepartmentPreviewItem[] = [
  { id: "d1", name: "Engineering", totalSpend: 500_000, changePct: 5.0, attentionState: "high" },
  { id: "d2", name: "Sales", totalSpend: 300_000, changePct: -2.0, attentionState: null },
];

describe("DashboardSummaryGrid", () => {
  it("renders all 4 summary cards", () => {
    render(<DashboardSummaryGrid cards={mockCards} timeRange="this_month" />);

    expect(screen.getByText("Total Spend")).toBeInTheDocument();
    expect(screen.getByText("Payroll Spend")).toBeInTheDocument();
    expect(screen.getByText("Claims Spend")).toBeInTheDocument();
    expect(screen.getByText("Attention Count")).toBeInTheDocument();
  });

  it("renders formatted currency values", () => {
    render(<DashboardSummaryGrid cards={mockCards} timeRange="this_month" />);

    expect(screen.getByText("$1,200,000")).toBeInTheDocument();
    expect(screen.getByText("$1,000,000")).toBeInTheDocument();
    expect(screen.getByText("$200,000")).toBeInTheDocument();
  });

  it("renders attention count with link to anomalies", () => {
    render(<DashboardSummaryGrid cards={mockCards} timeRange="this_month" />);

    const links = screen.getAllByRole("link");
    const attentionLink = links[0];
    expect(attentionLink).toHaveAttribute("href", "/dashboard/anomalies");
  });

  it("renders non-clickable cards without link wrapper", () => {
    const { container } = render(
      <DashboardSummaryGrid cards={mockCards} timeRange="this_month" />,
    );

    const links = container.querySelectorAll("a");
    expect(links).toHaveLength(1);
  });
});

describe("DashboardSummaryGridSkeleton", () => {
  it("renders 4 skeleton cards", () => {
    const { container } = render(<DashboardSummaryGridSkeleton />);
    const cards = container.querySelectorAll(".rounded-xl");
    expect(cards).toHaveLength(4);
  });
});

describe("DashboardAttentionItem", () => {
  it("renders department name and reason", () => {
    render(
      <DashboardAttentionItem item={mockAttentionItems[0]} timeRange="this_month" />,
    );

    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("Payroll spike")).toBeInTheDocument();
  });

  it("renders severity badge", () => {
    render(
      <DashboardAttentionItem item={mockAttentionItems[0]} timeRange="this_month" />,
    );

    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("renders change percentage chip", () => {
    render(
      <DashboardAttentionItem item={mockAttentionItems[0]} timeRange="this_month" />,
    );

    expect(screen.getByText("+15.0%")).toBeInTheDocument();
  });

  it("links to department detail with standard context", () => {
    render(
      <DashboardAttentionItem item={mockAttentionItems[0]} timeRange="this_month" />,
    );

    const link = screen.getByRole("link");
    expect(link).toHaveAttribute("href", "/dashboard/departments/d1?department_id=d1&source=dashboard_attention");
  });
});

describe("DashboardAttentionPanel", () => {
  it("renders attention items", () => {
    render(
      <DashboardAttentionPanel items={mockAttentionItems} timeRange="this_month" />,
    );

    expect(screen.getByText("Top Attention Items")).toBeInTheDocument();
    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("Marketing")).toBeInTheDocument();
  });

  it("renders View all anomalies CTA", () => {
    render(
      <DashboardAttentionPanel items={mockAttentionItems} timeRange="this_month" />,
    );

    expect(screen.getByText("View all anomalies →")).toBeInTheDocument();
  });

  it("renders empty state when no items", () => {
    render(<DashboardAttentionPanel items={[]} timeRange="this_month" />);

    expect(screen.getByText("No attention items")).toBeInTheDocument();
  });
});

describe("DashboardAiSummaryPanel", () => {
  it("renders headline and bullets", () => {
    render(<DashboardAiSummaryPanel summary={mockAiSummary} />);

    expect(screen.getByText("Spend overview for 2024-06")).toBeInTheDocument();
    expect(screen.getByText("Total spend: $1200k")).toBeInTheDocument();
    expect(screen.getByText("2 anomalies detected")).toBeInTheDocument();
  });

  it("renders AI badge", () => {
    render(<DashboardAiSummaryPanel summary={mockAiSummary} />);

    expect(screen.getByText("AI")).toBeInTheDocument();
    expect(screen.getByText("AI Summary")).toBeInTheDocument();
  });
});

describe("DashboardDepartmentPreview", () => {
  it("renders department rows with spend and change", () => {
    render(
      <DashboardDepartmentPreview departments={mockDeptPreview} timeRange="this_month" />,
    );

    expect(screen.getByText("Top Departments")).toBeInTheDocument();
    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("$500,000")).toBeInTheDocument();
    expect(screen.getByText("+5.0%")).toBeInTheDocument();
  });

  it("renders attention badge on departments with anomalies", () => {
    render(
      <DashboardDepartmentPreview departments={mockDeptPreview} timeRange="this_month" />,
    );

    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("renders View all departments CTA", () => {
    render(
      <DashboardDepartmentPreview departments={mockDeptPreview} timeRange="this_month" />,
    );

    expect(screen.getByText("View all departments →")).toBeInTheDocument();
  });

  it("links department rows to detail page", () => {
    render(
      <DashboardDepartmentPreview departments={mockDeptPreview} timeRange="this_month" />,
    );

    const links = screen.getAllByRole("link");
    const deptLink = links.find((l) => l.getAttribute("href")?.includes("departments/d1"));
    expect(deptLink).toBeDefined();
  });

  it("renders empty state when no departments", () => {
    render(<DashboardDepartmentPreview departments={[]} timeRange="this_month" />);

    expect(screen.getByText("No department data")).toBeInTheDocument();
  });
});
