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
  usePathname: () => "/dashboard/departments",
  useSearchParams: () => new URLSearchParams(),
}));

import { DepartmentRankedRow } from "@/components/departments/department-ranked-row";
import { DepartmentsFilterBar } from "@/components/departments/departments-filter-bar";
import type { DepartmentRankingItem } from "@/components/departments/department-list-mappers";

const mockItem: DepartmentRankingItem = {
  id: "d1",
  name: "Engineering",
  totalSpend: 500_000,
  payrollSpend: 400_000,
  claimsSpend: 100_000,
  changePct: 5.0,
  attentionState: "high",
};

const mockNoAttention: DepartmentRankingItem = {
  id: "d2",
  name: "Sales",
  totalSpend: 300_000,
  payrollSpend: 200_000,
  claimsSpend: 100_000,
  changePct: -2.0,
  attentionState: null,
};

describe("DepartmentRankedRow", () => {
  it("renders department name and formatted spend", () => {
    render(<DepartmentRankedRow item={mockItem} timeRange="this_month" />);
    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("$500,000")).toBeInTheDocument();
  });

  it("renders change percentage chip", () => {
    render(<DepartmentRankedRow item={mockItem} timeRange="this_month" />);
    expect(screen.getByText("+5.0%")).toBeInTheDocument();
  });

  it("renders attention badge when attentionState is set", () => {
    render(<DepartmentRankedRow item={mockItem} timeRange="this_month" />);
    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("does not render attention badge when null", () => {
    render(<DepartmentRankedRow item={mockNoAttention} timeRange="this_month" />);
    expect(screen.queryByText("high")).not.toBeInTheDocument();
  });

  it("applies stronger emphasis for attention-bearing rows", () => {
    render(<DepartmentRankedRow item={mockItem} timeRange="this_month" />);
    const nameEl = screen.getByText("Engineering");
    expect(nameEl.className).toContain("font-semibold");
  });

  it("links to department detail with ranking source", () => {
    render(<DepartmentRankedRow item={mockItem} timeRange="this_month" />);
    const link = screen.getByRole("link");
    expect(link).toHaveAttribute(
      "href",
      "/dashboard/departments/d1?department_id=d1&source=dashboard_ranking"
    );
  });
});

describe("DepartmentsFilterBar", () => {
  it("renders search input", () => {
    render(
      <DepartmentsFilterBar
        search="" attentionOnly={false} timeRange="this_month" activeSort="attention"
        onSearchChange={vi.fn()} onAttentionOnlyChange={vi.fn()}
        onTimeRangeChange={vi.fn()} onSortChange={vi.fn()}
      />
    );
    expect(screen.getByPlaceholderText("Search departments...")).toBeInTheDocument();
  });

  it("renders Attention only toggle", () => {
    render(
      <DepartmentsFilterBar
        search="" attentionOnly={false} timeRange="this_month" activeSort="attention"
        onSearchChange={vi.fn()} onAttentionOnlyChange={vi.fn()}
        onTimeRangeChange={vi.fn()} onSortChange={vi.fn()}
      />
    );
    expect(screen.getByText("Attention only")).toBeInTheDocument();
  });

  it("renders sort options", () => {
    render(
      <DepartmentsFilterBar
        search="" attentionOnly={false} timeRange="this_month" activeSort="attention"
        onSearchChange={vi.fn()} onAttentionOnlyChange={vi.fn()}
        onTimeRangeChange={vi.fn()} onSortChange={vi.fn()}
      />
    );
    expect(screen.getByText("Attention")).toBeInTheDocument();
    expect(screen.getByText("Total spend")).toBeInTheDocument();
    expect(screen.getByText("Change %")).toBeInTheDocument();
  });

  it("calls onSearchChange on input", () => {
    const onChange = vi.fn();
    render(
      <DepartmentsFilterBar
        search="" attentionOnly={false} timeRange="this_month" activeSort="attention"
        onSearchChange={onChange} onAttentionOnlyChange={vi.fn()}
        onTimeRangeChange={vi.fn()} onSortChange={vi.fn()}
      />
    );
    fireEvent.change(screen.getByPlaceholderText("Search departments..."), {
      target: { value: "eng" },
    });
    expect(onChange).toHaveBeenCalledWith("eng");
  });

  it("calls onSortChange when sort button clicked", () => {
    const onChange = vi.fn();
    render(
      <DepartmentsFilterBar
        search="" attentionOnly={false} timeRange="this_month" activeSort="attention"
        onSearchChange={vi.fn()} onAttentionOnlyChange={vi.fn()}
        onTimeRangeChange={vi.fn()} onSortChange={onChange}
      />
    );
    fireEvent.click(screen.getByText("Total spend"));
    expect(onChange).toHaveBeenCalledWith("total_spend");
  });
});
