import { describe, expect, it } from "vitest";
import { mapAnomalyListView, filterAnomalies } from "@/components/anomalies/anomaly-mappers";
import type { Anomaly } from "@/lib/api/types";

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
    severity: "high",
    change_pct: 12,
  },
  {
    id: "a3",
    department_id: "d2",
    department_name: "Sales",
    period: "2024-06",
    description: "Moderate payroll increase",
    severity: "medium",
    change_pct: 8,
  },
  {
    id: "a4",
    department_id: "d4",
    department_name: "HR",
    period: "2024-06",
    description: "Small claims uptick",
    severity: "low",
    change_pct: 3,
  },
  {
    id: "a5",
    department_id: "d5",
    department_name: "Finance",
    period: "2024-06",
    description: "Slight decrease",
    severity: "low",
    change_pct: -4,
  },
];

describe("mapAnomalyListView", () => {
  it("groups anomalies by severity", () => {
    const view = mapAnomalyListView(mockAnomalies);

    expect(view.groups).toHaveLength(3);
    expect(view.groups[0].severity).toBe("high");
    expect(view.groups[1].severity).toBe("medium");
    expect(view.groups[2].severity).toBe("low");
  });

  it("orders groups: high, medium, low", () => {
    const view = mapAnomalyListView(mockAnomalies);

    const severities = view.groups.map((g) => g.severity);
    expect(severities).toEqual(["high", "medium", "low"]);
  });

  it("sets correct counts per group", () => {
    const view = mapAnomalyListView(mockAnomalies);

    expect(view.groups[0].count).toBe(2);
    expect(view.groups[1].count).toBe(1);
    expect(view.groups[2].count).toBe(2);
  });

  it("maps anomaly fields to list items", () => {
    const view = mapAnomalyListView(mockAnomalies);

    const engItem = view.groups[0].items.find((i) => i.departmentName === "Engineering");
    expect(engItem).toBeDefined();
    expect(engItem!.reason).toBe("Payroll spike");
    expect(engItem!.changePct).toBe(15);
    expect(engItem!.departmentId).toBe("d1");
    expect(engItem!.severity).toBe("high");
  });

  it("excludes severity groups with no anomalies", () => {
    const single: Anomaly[] = [
      {
        id: "a1",
        department_id: "d1",
        department_name: "Engineering",
        period: "2024-06",
        description: "Spike",
        severity: "high",
        change_pct: 15,
      },
    ];

    const view = mapAnomalyListView(single);

    expect(view.groups).toHaveLength(1);
    expect(view.groups[0].severity).toBe("high");
  });

  it("sets snapshotId from first anomaly period", () => {
    const view = mapAnomalyListView(mockAnomalies);
    expect(view.snapshotId).toBe("2024-06");
  });

  it("handles empty list", () => {
    const view = mapAnomalyListView([]);

    expect(view.groups).toHaveLength(0);
    expect(view.snapshotId).toBe("");
  });
});

describe("filterAnomalies", () => {
  const items = mockAnomalies.map((a) => ({
    id: a.id,
    departmentId: a.department_id,
    departmentName: a.department_name,
    severity: a.severity,
    reason: a.description,
    changePct: a.change_pct,
    period: a.period,
  }));

  it("returns all items when no filter", () => {
    const result = filterAnomalies(items, null);
    expect(result).toHaveLength(5);
  });

  it("filters by severity", () => {
    const result = filterAnomalies(items, "high");
    expect(result).toHaveLength(2);
    expect(result.every((a) => a.severity === "high")).toBe(true);
  });

  it("filters by department", () => {
    const result = filterAnomalies(items, null, "d1");
    expect(result).toHaveLength(1);
    expect(result[0].departmentName).toBe("Engineering");
  });

  it("filters by severity and department together", () => {
    const result = filterAnomalies(items, "low", "d5");
    expect(result).toHaveLength(1);
    expect(result[0].departmentName).toBe("Finance");
    expect(result[0].severity).toBe("low");
  });

  it("returns empty when no matches", () => {
    const result = filterAnomalies(items, "high", "d5");
    expect(result).toHaveLength(0);
  });
});
