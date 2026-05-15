import { describe, expect, it } from "vitest";
import { mapToTrendChart, mapToDepartmentRanking, mapToClaimTypeBreakdown } from "@/lib/mappers";

describe("mapToTrendChart", () => {
  it("maps monthly trends to chart data format", () => {
    const input = [
      { month: "Jan", payroll: 100, claims: 50, total: 150 },
      { month: "Feb", payroll: 120, claims: 40, total: 160 },
    ];
    const result = mapToTrendChart(input);
    expect(result).toEqual([
      { month: "Jan", Payroll: 100, Claims: 50, Total: 150 },
      { month: "Feb", Payroll: 120, Claims: 40, Total: 160 },
    ]);
  });

  it("handles empty input", () => {
    expect(mapToTrendChart([])).toEqual([]);
  });
});

describe("mapToDepartmentRanking", () => {
  it("sorts departments by total spend descending", () => {
    const input = [
      { id: "1", name: "A", total_spend: 100, payroll_spend: 50, claims_spend: 50, change_pct: 0 },
      { id: "2", name: "B", total_spend: 300, payroll_spend: 200, claims_spend: 100, change_pct: 0 },
      { id: "3", name: "C", total_spend: 200, payroll_spend: 150, claims_spend: 50, change_pct: 0 },
    ];
    const result = mapToDepartmentRanking(input);
    expect(result.map((d) => d.name)).toEqual(["B", "C", "A"]);
  });
});

describe("mapToClaimTypeBreakdown", () => {
  it("sorts breakdowns by amount descending", () => {
    const input = [
      { type: "Travel", amount: 100, count: 2 },
      { type: "Supplies", amount: 300, count: 5 },
      { type: "Meals", amount: 200, count: 3 },
    ];
    const result = mapToClaimTypeBreakdown(input);
    expect(result.map((c) => c.type)).toEqual(["Supplies", "Meals", "Travel"]);
  });
});
