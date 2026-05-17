import { describe, expect, it } from "vitest";
import { mapDepartmentDetailView } from "@/components/department-detail/department-detail-mappers";
import type {
  DepartmentDetail,
  EmployeeContribution,
  ClaimDetail,
  MonthlyTrend,
  Anomaly,
} from "@/lib/api/types";

const mockDepartment: DepartmentDetail = {
  id: "d1",
  name: "Engineering",
  payroll_spend: 400_000,
  claims_spend: 100_000,
  total_spend: 500_000,
  change_pct: 5.0,
  employee_count: 42,
};

const mockEmployees: EmployeeContribution[] = [
  { id: "e1", name: "Alice", department: "Engineering", payroll: 120_000, claims: 10_000, total: 130_000 },
  { id: "e2", name: "Bob", department: "Engineering", payroll: 110_000, claims: 5_000, total: 115_000 },
  { id: "e3", name: "Carol", department: "Engineering", payroll: 100_000, claims: 30_000, total: 130_000 },
  { id: "e4", name: "Dave", department: "Engineering", payroll: 50_000, claims: 2_000, total: 52_000 },
  { id: "e5", name: "Eve", department: "Engineering", payroll: 60_000, claims: 1_000, total: 61_000 },
  { id: "e6", name: "Frank", department: "Engineering", payroll: 30_000, claims: 0, total: 30_000 },
];

const mockClaims: ClaimDetail[] = [
  { id: "c1", employee_name: "Alice", department: "Engineering", type: "Medical", amount: 5_000, date: "2024-06-01" },
  { id: "c2", employee_name: "Carol", department: "Engineering", type: "Medical", amount: 20_000, date: "2024-06-05" },
  { id: "c3", employee_name: "Bob", department: "Engineering", type: "Dental", amount: 5_000, date: "2024-06-10" },
  { id: "c4", employee_name: "Alice", department: "Engineering", type: "Vision", amount: 5_000, date: "2024-06-12" },
  { id: "c5", employee_name: "Carol", department: "Engineering", type: "Pharmacy", amount: 10_000, date: "2024-06-15" },
];

const mockTrends: MonthlyTrend[] = [
  { month: "2024-01", payroll: 380_000, claims: 90_000, total: 470_000 },
  { month: "2024-02", payroll: 390_000, claims: 95_000, total: 485_000 },
  { month: "2024-03", payroll: 400_000, claims: 100_000, total: 500_000 },
];

const mockAnomalies: Anomaly[] = [
  { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Payroll spike", severity: "high", change_pct: 15 },
  { id: "a2", department_id: "d2", department_name: "Sales", period: "2024-06", description: "Sales drop", severity: "medium", change_pct: -8 },
];

describe("mapDepartmentDetailView", () => {
  it("maps department summary fields", () => {
    const view = mapDepartmentDetailView(
      mockDepartment, mockEmployees, [], mockTrends, mockAnomalies, "this_month",
    );

    expect(view.department.name).toBe("Engineering");
    expect(view.department.id).toBe("d1");
    expect(view.summary.totalSpend).toBe(500_000);
    expect(view.summary.changePercent).toBe(5.0);
  });

  it("attaches attention state from anomalies", () => {
    const view = mapDepartmentDetailView(
      mockDepartment, mockEmployees, [], mockTrends, mockAnomalies, "this_month",
    );

    expect(view.department.attentionState).toBe("high");
  });

  it("returns null attentionState when no anomalies for department", () => {
    const noDeptAnomalies: Anomaly[] = [
      { id: "a2", department_id: "d2", department_name: "Sales", period: "2024-06", description: "Sales drop", severity: "medium", change_pct: -8 },
    ];

    const view = mapDepartmentDetailView(
      mockDepartment, mockEmployees, [], mockTrends, noDeptAnomalies, "this_month",
    );

    expect(view.department.attentionState).toBeNull();
  });

  it("selects highest severity when multiple anomalies for same department", () => {
    const multiAnomalies: Anomaly[] = [
      { id: "a1", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "Low spike", severity: "low", change_pct: 5 },
      { id: "a3", department_id: "d1", department_name: "Engineering", period: "2024-06", description: "High spike", severity: "high", change_pct: 25 },
    ];

    const view = mapDepartmentDetailView(
      mockDepartment, mockEmployees, [], mockTrends, multiAnomalies, "this_month",
    );

    expect(view.department.attentionState).toBe("high");
  });

  it("returns top 5 employees sorted by total descending", () => {
    const view = mapDepartmentDetailView(
      mockDepartment, mockEmployees, [], mockTrends, mockAnomalies, "this_month",
    );

    expect(view.topEmployees).toHaveLength(5);
    expect(view.topEmployees[0].total).toBeGreaterThanOrEqual(view.topEmployees[1].total);
    expect(view.topEmployees[0].name).toMatch(/Alice|Carol/);
  });

  it("aggregates claim types from claim details", () => {
    const view = mapDepartmentDetailView(
      mockDepartment, mockEmployees, mockClaims, mockTrends, mockAnomalies, "this_month",
    );

    expect(view.topClaimTypes.length).toBeGreaterThan(0);
    const medicalType = view.topClaimTypes.find((ct) => ct.name === "Medical");
    expect(medicalType).toBeDefined();
    expect(medicalType!.total).toBe(25_000);
  });

  it("sorts claim types by total descending", () => {
    const view = mapDepartmentDetailView(
      mockDepartment, mockEmployees, mockClaims, mockTrends, mockAnomalies, "this_month",
    );

    for (let i = 1; i < view.topClaimTypes.length; i++) {
      expect(view.topClaimTypes[i - 1].total).toBeGreaterThanOrEqual(view.topClaimTypes[i].total);
    }
  });

  it("returns empty trend series when no trend data", () => {
    const view = mapDepartmentDetailView(
      mockDepartment, mockEmployees, [], [], mockAnomalies, "this_month",
    );

    expect(view.trend).toHaveLength(0);
  });

  it("maps trends into series with Total, Payroll, Claims labels", () => {
    const view = mapDepartmentDetailView(
      mockDepartment, mockEmployees, [], mockTrends, mockAnomalies, "this_month",
    );

    expect(view.trend).toHaveLength(3);
    expect(view.trend[0].label).toBe("Total");
    expect(view.trend[1].label).toBe("Payroll");
    expect(view.trend[2].label).toBe("Claims");
    expect(view.trend[0].data).toHaveLength(3);
    expect(view.trend[0].data[0].month).toBe("2024-01");
    expect(view.trend[0].data[0].value).toBe(470_000);
  });

  it("generates aiSummary with headline and bullets", () => {
    const view = mapDepartmentDetailView(
      mockDepartment, mockEmployees, mockClaims, mockTrends, mockAnomalies, "this_month",
    );

    expect(view.aiSummary.headline).toContain("Engineering");
    expect(view.aiSummary.headline).toContain("high");
    expect(view.aiSummary.bullets).toHaveLength(3);
    expect(view.aiSummary.bullets[0]).toContain("Alice");
  });

  it("handles empty employees gracefully", () => {
    const view = mapDepartmentDetailView(
      mockDepartment, [], [], mockTrends, mockAnomalies, "this_month",
    );

    expect(view.topEmployees).toHaveLength(0);
    expect(view.aiSummary.headline).toContain("Engineering");
  });

  it("handles negative change percent", () => {
    const dept: DepartmentDetail = { ...mockDepartment, change_pct: -3.5 };

    const view = mapDepartmentDetailView(
      dept, mockEmployees, [], mockTrends, mockAnomalies, "this_month",
    );

    expect(view.summary.changePercent).toBe(-3.5);
  });

  it("preserves timeRange in view", () => {
    const view = mapDepartmentDetailView(
      mockDepartment, mockEmployees, [], mockTrends, mockAnomalies, "last_3_months",
    );

    expect(view.timeRange).toBe("last_3_months");
  });
});
