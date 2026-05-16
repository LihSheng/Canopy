import { describe, expect, it } from "vitest";
import { mapCommandView } from "@/components/dashboard-v2/dashboard-mappers";
import type {
  DashboardSummary,
  DepartmentSummary,
  MonthlyTrend,
  ClaimTypeBreakdown,
  Anomaly,
} from "@/lib/api/types";

const mockSummary: DashboardSummary = {
  total_payroll: 1_000_000,
  total_claims: 200_000,
  period: { year: 2024, month: 6 },
  department_count: 5,
  anomaly_count: 2,
  last_updated: "2024-06-15T10:00:00Z",
};

const mockDepartments: DepartmentSummary[] = [
  {
    id: "d1",
    name: "Engineering",
    total_spend: 500_000,
    payroll_spend: 400_000,
    claims_spend: 100_000,
    change_pct: 5.0,
  },
  {
    id: "d2",
    name: "Sales",
    total_spend: 300_000,
    payroll_spend: 200_000,
    claims_spend: 100_000,
    change_pct: -2.0,
  },
  {
    id: "d3",
    name: "Marketing",
    total_spend: 200_000,
    payroll_spend: 150_000,
    claims_spend: 50_000,
    change_pct: 12.0,
  },
  {
    id: "d4",
    name: "HR",
    total_spend: 150_000,
    payroll_spend: 120_000,
    claims_spend: 30_000,
    change_pct: 0.0,
  },
  {
    id: "d5",
    name: "Finance",
    total_spend: 120_000,
    payroll_spend: 100_000,
    claims_spend: 20_000,
    change_pct: -8.0,
  },
];

const mockTrends: MonthlyTrend[] = [
  { month: "2024-01", payroll: 900_000, claims: 180_000, total: 1_080_000 },
  { month: "2024-02", payroll: 950_000, claims: 190_000, total: 1_140_000 },
  { month: "2024-03", payroll: 1_000_000, claims: 200_000, total: 1_200_000 },
];

const mockClaimTypes: ClaimTypeBreakdown[] = [
  { type: "Travel", amount: 100_000, count: 50 },
  { type: "Meals", amount: 50_000, count: 30 },
];

const mockAnomalies: Anomaly[] = [
  {
    id: "a1",
    department_id: "d1",
    department_name: "Engineering",
    period: "2024-06",
    description: "Payroll spike",
    severity: "high",
    change_pct: 15,
  },
  {
    id: "a2",
    department_id: "d3",
    department_name: "Marketing",
    period: "2024-06",
    description: "Unusual claims",
    severity: "medium",
    change_pct: 12,
  },
];

describe("mapCommandView", () => {
  it("returns correct snapshot metadata", () => {
    const view = mapCommandView(
      mockSummary,
      mockDepartments,
      mockTrends,
      mockClaimTypes,
      mockAnomalies,
      "this_month",
    );

    expect(view.snapshotId).toBe("2024-06-15T10:00:00Z");
    expect(view.snapshotLabel).toBe("2024-06");
    expect(view.timeRange).toBe("this_month");
  });

  it("computes total spend summary card correctly", () => {
    const view = mapCommandView(
      mockSummary,
      mockDepartments,
      mockTrends,
      mockClaimTypes,
      mockAnomalies,
      "this_month",
    );

    expect(view.summaryCards.totalSpend.value).toBe(1_200_000);
    expect(view.summaryCards.totalSpend.label).toBe("Total Spend");
    expect(view.summaryCards.totalSpend.clickable).toBe(false);
  });

  it("sets attention count card to clickable", () => {
    const view = mapCommandView(
      mockSummary,
      mockDepartments,
      mockTrends,
      mockClaimTypes,
      mockAnomalies,
      "this_month",
    );

    expect(view.summaryCards.attentionCount.value).toBe(2);
    expect(view.summaryCards.attentionCount.clickable).toBe(true);
  });

  it("maps top 3 attention items from anomalies", () => {
    const extraAnomalies: Anomaly[] = [
      ...mockAnomalies,
      {
        id: "a3",
        department_id: "d2",
        department_name: "Sales",
        period: "2024-06",
        description: "Decreased claims",
        severity: "low",
        change_pct: -5,
      },
      {
        id: "a4",
        department_id: "d4",
        department_name: "HR",
        period: "2024-06",
        description: "Minor spike",
        severity: "low",
        change_pct: 3,
      },
    ];

    const view = mapCommandView(
      mockSummary,
      mockDepartments,
      mockTrends,
      mockClaimTypes,
      extraAnomalies,
      "this_month",
    );

    expect(view.topAttentionItems).toHaveLength(3);
    expect(view.topAttentionItems[0].departmentName).toBe("Engineering");
    expect(view.topAttentionItems[0].severity).toBe("high");
    expect(view.topAttentionItems[0].reason).toBe("Payroll spike");
    expect(view.topAttentionItems[0].changePct).toBe(15);
  });

  it("builds AI summary with headline and bullets", () => {
    const view = mapCommandView(
      mockSummary,
      mockDepartments,
      mockTrends,
      mockClaimTypes,
      mockAnomalies,
      "this_month",
    );

    expect(view.aiSummary.headline).toContain("2024-06");
    expect(view.aiSummary.bullets).toHaveLength(3);
    expect(view.aiSummary.bullets[0]).toContain("1200k");
  });

  it("maps trend series with correct labels", () => {
    const view = mapCommandView(
      mockSummary,
      mockDepartments,
      mockTrends,
      mockClaimTypes,
      mockAnomalies,
      "this_month",
    );

    expect(view.trendSeries).toHaveLength(3);
    expect(view.trendSeries[0].label).toBe("Total");
    expect(view.trendSeries[1].label).toBe("Payroll");
    expect(view.trendSeries[2].label).toBe("Claims");
  });

  it("maps trend data points correctly", () => {
    const view = mapCommandView(
      mockSummary,
      mockDepartments,
      mockTrends,
      mockClaimTypes,
      mockAnomalies,
      "this_month",
    );

    const totalSeries = view.trendSeries[0];
    expect(totalSeries.data).toHaveLength(3);
    expect(totalSeries.data[0]).toEqual({ month: "2024-01", value: 1_080_000 });
    expect(totalSeries.data[1]).toEqual({ month: "2024-02", value: 1_140_000 });
    expect(totalSeries.data[2]).toEqual({ month: "2024-03", value: 1_200_000 });
  });

  it("maps top 5 departments with attention state", () => {
    const view = mapCommandView(
      mockSummary,
      mockDepartments,
      mockTrends,
      mockClaimTypes,
      mockAnomalies,
      "this_month",
    );

    expect(view.topDepartments).toHaveLength(5);
    expect(view.topDepartments[0].name).toBe("Engineering");
    expect(view.topDepartments[0].attentionState).toBe("high");
    expect(view.topDepartments[0].changePct).toBe(5.0);
  });

  it("sets attention state to null for departments without anomalies", () => {
    const view = mapCommandView(
      mockSummary,
      mockDepartments,
      mockTrends,
      mockClaimTypes,
      mockAnomalies,
      "this_month",
    );

    expect(view.topDepartments[1].name).toBe("Sales");
    expect(view.topDepartments[1].attentionState).toBeNull();
  });

  it("handles empty data gracefully", () => {
    const emptySummary: DashboardSummary = {
      total_payroll: 0,
      total_claims: 0,
      period: { year: 2024, month: 1 },
      department_count: 0,
      anomaly_count: 0,
      last_updated: "",
    };

    const view = mapCommandView(
      emptySummary,
      [],
      [],
      [],
      [],
      "this_month",
    );

    expect(view.summaryCards.totalSpend.value).toBe(0);
    expect(view.topAttentionItems).toHaveLength(0);
    expect(view.trendSeries[0].data).toHaveLength(0);
    expect(view.topDepartments).toHaveLength(0);
  });
});
