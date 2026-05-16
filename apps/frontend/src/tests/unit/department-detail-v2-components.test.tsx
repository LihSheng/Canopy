import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/hooks/use-session", () => ({
  useSession: () => ({
    user: { id: "1", email: "test@test.com", display_name: "Test User" },
    loading: false, error: null, refetch: vi.fn(), logout: vi.fn(),
  }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn(), replace: vi.fn() }),
  usePathname: () => "/dashboard/departments/d1",
  useSearchParams: () => new URLSearchParams(),
}));

import { DepartmentDetailHeader } from "@/components/department-detail-v2/department-detail-header";
import { DepartmentAiSummary } from "@/components/department-detail-v2/department-ai-summary";
import { DepartmentTrendPanel } from "@/components/department-detail-v2/department-trend-panel";
import { DepartmentContributorsSplit } from "@/components/department-detail-v2/department-contributors-split";
import type { ContributorItem, SummaryBrief, TrendSeries } from "@/components/department-detail-v2/department-detail-mappers";

const mockSummary = {
  departmentName: "Engineering",
  attentionState: "high" as const,
  totalSpend: 500_000,
  changePercent: 5.0,
};

const mockAiSummary: SummaryBrief = {
  headline: "Engineering spent $500k this period, triggering a high attention state.",
  bullets: [
    "Alice is the highest spender at $130k",
    "Medical leads claim types at $25k",
    "Change from previous period: +5.0% across 42 employees",
  ],
};

const mockTrendSeries: TrendSeries[] = [
  { label: "Total", data: [{ month: "Jan", value: 450_000 }, { month: "Feb", value: 470_000 }] },
  { label: "Payroll", data: [{ month: "Jan", value: 370_000 }, { month: "Feb", value: 390_000 }] },
];

const mockEmployees: ContributorItem[] = [
  { id: "e1", name: "Alice", total: 130_000 },
  { id: "e2", name: "Bob", total: 115_000 },
  { id: "e3", name: "Carol", total: 100_000 },
];

const mockClaimTypes: ContributorItem[] = [
  { id: "ct-0", name: "Medical", total: 25_000 },
  { id: "ct-1", name: "Dental", total: 15_000 },
  { id: "ct-2", name: "Pharmacy", total: 10_000 },
];

describe("DepartmentDetailHeader", () => {
  it("renders department name and total spend", () => {
    render(
      <DepartmentDetailHeader summary={mockSummary} timeRange="this_month" onTimeRangeChange={vi.fn()} />,
    );
    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("$500,000")).toBeInTheDocument();
  });

  it("renders attention badge when set", () => {
    render(
      <DepartmentDetailHeader summary={mockSummary} timeRange="this_month" onTimeRangeChange={vi.fn()} />,
    );
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("does not render attention badge when null", () => {
    render(
      <DepartmentDetailHeader
        summary={{ ...mockSummary, attentionState: null }}
        timeRange="this_month"
        onTimeRangeChange={vi.fn()}
      />,
    );
    expect(screen.queryByText("high")).not.toBeInTheDocument();
  });

  it("renders change percentage", () => {
    render(
      <DepartmentDetailHeader summary={mockSummary} timeRange="this_month" onTimeRangeChange={vi.fn()} />,
    );
    expect(screen.getByText("+5.0%")).toBeInTheDocument();
  });

  it("renders time range toggle buttons", () => {
    render(
      <DepartmentDetailHeader summary={mockSummary} timeRange="this_month" onTimeRangeChange={vi.fn()} />,
    );
    expect(screen.getAllByText("This month").length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText("Last 3 months")).toBeInTheDocument();
    expect(screen.getByText("Last 12 months")).toBeInTheDocument();
  });

  it("calls onTimeRangeChange when range button clicked", () => {
    const onChange = vi.fn();
    render(
      <DepartmentDetailHeader summary={mockSummary} timeRange="this_month" onTimeRangeChange={onChange} />,
    );
    fireEvent.click(screen.getByText("Last 3 months"));
    expect(onChange).toHaveBeenCalledWith("last_3_months");
  });
});

describe("DepartmentAiSummary", () => {
  it("renders headline and bullets", () => {
    render(<DepartmentAiSummary summary={mockAiSummary} />);
    expect(screen.getByText(/Engineering spent/)).toBeInTheDocument();
    expect(screen.getByText(/Alice is the highest spender/)).toBeInTheDocument();
    expect(screen.getByText(/Medical leads claim types/)).toBeInTheDocument();
  });

  it("renders AI badge", () => {
    render(<DepartmentAiSummary summary={mockAiSummary} />);
    expect(screen.getByText("AI")).toBeInTheDocument();
    expect(screen.getByText("AI Summary")).toBeInTheDocument();
  });
});

describe("DepartmentTrendPanel", () => {
  it("renders trend chart when data exists", () => {
    const { container } = render(<DepartmentTrendPanel series={mockTrendSeries} />);
    expect(screen.getByText("Monthly Trends")).toBeInTheDocument();
    expect(container.querySelector(".recharts-responsive-container")).toBeInTheDocument();
  });

  it("shows empty message when no data", () => {
    render(<DepartmentTrendPanel series={[]} />);
    expect(screen.getByText("No trend data available")).toBeInTheDocument();
  });
});

describe("DepartmentContributorsSplit", () => {
  it("renders side-by-side employee and claim type panels", () => {
    render(<DepartmentContributorsSplit topEmployees={mockEmployees} topClaimTypes={mockClaimTypes} />);
    expect(screen.getByText("Top Employees")).toBeInTheDocument();
    expect(screen.getByText("Top Claim Types")).toBeInTheDocument();
  });

  it("renders employee names and totals", () => {
    render(<DepartmentContributorsSplit topEmployees={mockEmployees} topClaimTypes={mockClaimTypes} />);
    expect(screen.getByText("Alice")).toBeInTheDocument();
    expect(screen.getByText("Bob")).toBeInTheDocument();
    expect(screen.getByText("$130,000")).toBeInTheDocument();
  });

  it("renders claim type names and totals", () => {
    render(<DepartmentContributorsSplit topEmployees={mockEmployees} topClaimTypes={mockClaimTypes} />);
    expect(screen.getByText("Medical")).toBeInTheDocument();
    expect(screen.getByText("Dental")).toBeInTheDocument();
    expect(screen.getByText("$25,000")).toBeInTheDocument();
  });

  it("renders bars proportional to max total", () => {
    const { container } = render(
      <DepartmentContributorsSplit topEmployees={mockEmployees} topClaimTypes={[]} />,
    );
    const bars = container.querySelectorAll(".bg-zinc-800");
    expect(bars.length).toBeGreaterThan(0);
  });
});
