import { render, screen, fireEvent } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/hooks/use-session", async () => {
  const { createSessionMock } = await import("@/tests/mocks/session");
  return { useSession: () => createSessionMock() };
});

vi.mock("next/navigation", async () => {
  const { createRouterMock } = await import("@/tests/mocks/navigation");
  return createRouterMock({ pathname: "/dashboard/anomalies" });
});

import { AnomalyRow } from "@/components/anomalies/anomaly-row";
import { AnomaliesGroup } from "@/components/anomalies/anomalies-group";
import { AnomaliesFilterBar } from "@/components/anomalies/anomalies-filter-bar";
import type { AnomalyListItem, AnomalyGroup } from "@/components/anomalies/anomaly-mappers";

const mockItem: AnomalyListItem = {
  id: "a1",
  departmentId: "d1",
  departmentName: "Engineering",
  severity: "high",
  reason: "Payroll spike",
  changePct: 15,
  period: "2024-06",
};

const mockGroup: AnomalyGroup = {
  severity: "high",
  count: 2,
  items: [
    mockItem,
    {
      id: "a2",
      departmentId: "d3",
      departmentName: "Marketing",
      severity: "high",
      reason: "Unusual claims",
      changePct: 12,
      period: "2024-06",
    },
  ],
};

const mockMediumGroup: AnomalyGroup = {
  severity: "medium",
  count: 1,
  items: [
    {
      id: "a3",
      departmentId: "d2",
      departmentName: "Sales",
      severity: "medium",
      reason: "Moderate payroll increase",
      changePct: 8,
      period: "2024-06",
    },
  ],
};

describe("AnomalyRow", () => {
  it("renders department name and reason", () => {
    render(<AnomalyRow item={mockItem} timeRange="this_month" />);

    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("Payroll spike")).toBeInTheDocument();
  });

  it("renders severity badge", () => {
    render(<AnomalyRow item={mockItem} timeRange="this_month" />);

    expect(screen.getByText("high")).toBeInTheDocument();
  });

  it("renders change percentage chip", () => {
    render(<AnomalyRow item={mockItem} timeRange="this_month" />);

    expect(screen.getByText("+15.0%")).toBeInTheDocument();
  });

  it("links to department detail with anomaly context", () => {
    render(<AnomalyRow item={mockItem} timeRange="this_month" />);

    const link = screen.getByRole("link");
    expect(link).toHaveAttribute(
      "href",
      "/dashboard/departments/d1?department_id=d1&source=anomalies&anomaly_id=a1",
    );
  });
});

describe("AnomaliesGroup", () => {
  it("renders severity label and count", () => {
    render(
      <AnomaliesGroup group={mockGroup} timeRange="this_month" expandedByDefault />,
    );

    expect(screen.getByText("High severity")).toBeInTheDocument();
    expect(screen.getByText("2")).toBeInTheDocument();
  });

  it("expands by default when expandedByDefault is true", () => {
    render(
      <AnomaliesGroup group={mockGroup} timeRange="this_month" expandedByDefault />,
    );

    expect(screen.getByText("Engineering")).toBeInTheDocument();
    expect(screen.getByText("Marketing")).toBeInTheDocument();
  });

  it("starts collapsed when expandedByDefault is false", () => {
    render(
      <AnomaliesGroup group={mockGroup} timeRange="this_month" expandedByDefault={false} />,
    );

    expect(screen.queryByText("Engineering")).not.toBeInTheDocument();
    expect(screen.queryByText("Marketing")).not.toBeInTheDocument();
  });

  it("toggles collapse and expand on click", () => {
    render(
      <AnomaliesGroup group={mockGroup} timeRange="this_month" expandedByDefault />,
    );

    expect(screen.getByText("Engineering")).toBeInTheDocument();

    const toggle = screen.getByRole("button");
    fireEvent.click(toggle);

    expect(screen.queryByText("Engineering")).not.toBeInTheDocument();

    fireEvent.click(toggle);

    expect(screen.getByText("Engineering")).toBeInTheDocument();
  });

  it("has aria-expanded attribute", () => {
    render(
      <AnomaliesGroup group={mockGroup} timeRange="this_month" expandedByDefault />,
    );

    const button = screen.getByRole("button");
    expect(button).toHaveAttribute("aria-expanded", "true");
  });

  it("renders medium severity label correctly", () => {
    render(
      <AnomaliesGroup group={mockMediumGroup} timeRange="this_month" expandedByDefault />,
    );

    expect(screen.getByText("Medium severity")).toBeInTheDocument();
  });
});

describe("AnomaliesFilterBar", () => {
  it("renders time range options", () => {
    render(
      <AnomaliesFilterBar
        timeRange="this_month"
        severity={null}
        onTimeRangeChange={vi.fn()}
        onSeverityChange={vi.fn()}
      />,
    );

    expect(screen.getByText("This month")).toBeInTheDocument();
    expect(screen.getByText("Last 3 months")).toBeInTheDocument();
    expect(screen.getByText("Last 12 months")).toBeInTheDocument();
  });

  it("renders severity options", () => {
    render(
      <AnomaliesFilterBar
        timeRange="this_month"
        severity={null}
        onTimeRangeChange={vi.fn()}
        onSeverityChange={vi.fn()}
      />,
    );

    expect(screen.getByText("All")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByText("Medium")).toBeInTheDocument();
    expect(screen.getByText("Low")).toBeInTheDocument();
  });

  it("calls onTimeRangeChange when a range option is clicked", () => {
    const onChange = vi.fn();
    render(
      <AnomaliesFilterBar
        timeRange="this_month"
        severity={null}
        onTimeRangeChange={onChange}
        onSeverityChange={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByText("Last 3 months"));
    expect(onChange).toHaveBeenCalledWith("last_3_months");
  });

  it("calls onSeverityChange when a severity option is clicked", () => {
    const onChange = vi.fn();
    render(
      <AnomaliesFilterBar
        timeRange="this_month"
        severity={null}
        onTimeRangeChange={vi.fn()}
        onSeverityChange={onChange}
      />,
    );

    fireEvent.click(screen.getAllByText("High")[0]);
    expect(onChange).toHaveBeenCalledWith("high");
  });

  it("shows department filter badge when departmentId is set", () => {
    render(
      <AnomaliesFilterBar
        timeRange="this_month"
        severity={null}
        departmentId="d1"
        onTimeRangeChange={vi.fn()}
        onSeverityChange={vi.fn()}
      />,
    );

    expect(screen.getByText("Department filter active")).toBeInTheDocument();
  });
});
