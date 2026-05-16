import { describe, expect, it } from "vitest";
import {
  attachAttentionState,
  sortItems,
  filterDepartments,
} from "@/components/departments-v2/department-list-mappers";
import type { DepartmentSummary, Anomaly } from "@/lib/api/types";

const mockDepartments: DepartmentSummary[] = [
  { id: "d1", name: "Engineering", total_spend: 500_000, payroll_spend: 400_000, claims_spend: 100_000, change_pct: 5.0 },
  { id: "d2", name: "Sales", total_spend: 300_000, payroll_spend: 200_000, claims_spend: 100_000, change_pct: -2.0 },
  { id: "d3", name: "Marketing", total_spend: 200_000, payroll_spend: 150_000, claims_spend: 50_000, change_pct: 12.0 },
  { id: "d4", name: "HR", total_spend: 150_000, payroll_spend: 120_000, claims_spend: 30_000, change_pct: 0.0 },
  { id: "d5", name: "Finance", total_spend: 120_000, payroll_spend: 100_000, claims_spend: 20_000, change_pct: -8.0 },
];

const mockAnomalies: Anomaly[] = [
  { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike", severity: "high", change_pct: 15 },
  { id: "a2", department_id: "d3", department_name: "Marketing", period: "2024-06", description: "Unusual claims", severity: "medium", change_pct: 12 },
];

describe("attachAttentionState", () => {
  it("attaches attention states from anomalies", () => {
    const items = attachAttentionState(mockDepartments, mockAnomalies);

    expect(items[0].attentionState).toBe("high");
    expect(items[1].attentionState).toBeNull();
    expect(items[2].attentionState).toBe("medium");
    expect(items[3].attentionState).toBeNull();
    expect(items[4].attentionState).toBeNull();
  });

  it("maps all department fields", () => {
    const items = attachAttentionState(mockDepartments, mockAnomalies);

    expect(items[0].name).toBe("Engineering");
    expect(items[0].totalSpend).toBe(500_000);
    expect(items[0].changePct).toBe(5.0);
  });

  it("uses highest severity when multiple anomalies exist for one department", () => {
    const multiAnomalies: Anomaly[] = [
      { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike", severity: "low", change_pct: 15 },
      { id: "a2", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Claims spike", severity: "high", change_pct: 25 },
    ];

    const items = attachAttentionState(mockDepartments, multiAnomalies);
    expect(items[0].attentionState).toBe("high");
  });

  it("returns all items with null attention when no anomalies", () => {
    const items = attachAttentionState(mockDepartments, []);
    expect(items.every((i) => i.attentionState === null)).toBe(true);
  });
});

describe("sortItems", () => {
  const items = attachAttentionState(mockDepartments, mockAnomalies);

  it("sorts by attention by default (high first, then medium, then null)", () => {
    const sorted = sortItems(items, "attention");
    expect(sorted[0].attentionState).toBe("high");
    expect(sorted[1].attentionState).toBe("medium");
    expect(sorted[2].attentionState).toBeNull();
  });

  it("sorts by total spend descending", () => {
    const sorted = sortItems(items, "total_spend");
    expect(sorted[0].totalSpend).toBe(500_000);
    expect(sorted[1].totalSpend).toBe(300_000);
    expect(sorted[sorted.length - 1].totalSpend).toBe(120_000);
  });

  it("sorts by change percent absolute descending", () => {
    const sorted = sortItems(items, "change_percent");
    expect(sorted[0].changePct).toBe(12.0);
    expect(sorted[1].changePct).toBe(-8.0);
  });
});

describe("filterDepartments", () => {
  const items = attachAttentionState(mockDepartments, mockAnomalies);

  it("returns all items with no filters", () => {
    const result = filterDepartments(items, "", false);
    expect(result).toHaveLength(5);
  });

  it("filters by search text", () => {
    const result = filterDepartments(items, "eng", false);
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe("Engineering");
  });

  it("filters attention-only", () => {
    const result = filterDepartments(items, "", true);
    expect(result).toHaveLength(2);
    expect(result.every((i) => i.attentionState !== null)).toBe(true);
  });

  it("combines search and attention filter", () => {
    const result = filterDepartments(items, "mark", true);
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe("Marketing");
  });

  it("is case-insensitive for search", () => {
    const result = filterDepartments(items, "SALES", false);
    expect(result).toHaveLength(1);
    expect(result[0].name).toBe("Sales");
  });
});
