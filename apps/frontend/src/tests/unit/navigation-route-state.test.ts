import { describe, expect, it } from "vitest";
import {
  readDashboardState,
  readAnomalyState,
  readDepartmentDetailState,
  writeDashboardState,
  writeAnomalyState,
  writeDepartmentDetailState,
} from "@/lib/navigation/route-state";

describe("readDashboardState", () => {
  it("parses empty params with default time range", () => {
    const params = new URLSearchParams();
    const state = readDashboardState(params);
    expect(state.timeRange).toBe("this_month");
  });

  it("parses explicit time range", () => {
    const params = new URLSearchParams("range=last_3_months");
    const state = readDashboardState(params);
    expect(state.timeRange).toBe("last_3_months");
  });

  it("falls back for unknown range value", () => {
    const params = new URLSearchParams("range=unknown");
    const state = readDashboardState(params);
    expect(state.timeRange).toBe("this_month");
  });
});

describe("readAnomalyState", () => {
  it("parses time range from params", () => {
    const params = new URLSearchParams("range=last_12_months");
    const state = readAnomalyState(params);
    expect(state.timeRange).toBe("last_12_months");
  });

  it("parses department prefilter", () => {
    const params = new URLSearchParams("department_id=eng");
    const state = readAnomalyState(params);
    expect(state.departmentId).toBe("eng");
  });

  it("parses valid severity", () => {
    const params = new URLSearchParams("severity=high");
    const state = readAnomalyState(params);
    expect(state.severity).toBe("high");
  });

  it("ignores invalid severity", () => {
    const params = new URLSearchParams("severity=critical");
    const state = readAnomalyState(params);
    expect(state.severity).toBeUndefined();
  });

  it("parses all fields together", () => {
    const params = new URLSearchParams(
      "range=last_3_months&department_id=sales&severity=medium",
    );
    const state = readAnomalyState(params);
    expect(state.timeRange).toBe("last_3_months");
    expect(state.departmentId).toBe("sales");
    expect(state.severity).toBe("medium");
  });

  it("returns undefined for missing optional fields", () => {
    const params = new URLSearchParams();
    const state = readAnomalyState(params);
    expect(state.departmentId).toBeUndefined();
    expect(state.severity).toBeUndefined();
  });
});

describe("readDepartmentDetailState", () => {
  it("parses department id", () => {
    const params = new URLSearchParams("department_id=eng");
    const state = readDepartmentDetailState(params);
    expect(state.departmentId).toBe("eng");
  });

  it("parses source context", () => {
    const params = new URLSearchParams(
      "department_id=eng&source=dashboard_attention",
    );
    const state = readDepartmentDetailState(params);
    expect(state.source).toBe("dashboard_attention");
  });

  it("parses anomaly id", () => {
    const params = new URLSearchParams(
      "department_id=eng&anomaly_id=a1",
    );
    const state = readDepartmentDetailState(params);
    expect(state.anomalyId).toBe("a1");
  });

  it("ignores invalid source", () => {
    const params = new URLSearchParams(
      "department_id=eng&source=unknown",
    );
    const state = readDepartmentDetailState(params);
    expect(state.source).toBeUndefined();
  });

  it("returns empty department id when missing", () => {
    const params = new URLSearchParams();
    const state = readDepartmentDetailState(params);
    expect(state.departmentId).toBe("");
  });
});

describe("writeDashboardState", () => {
  it("omits default time range", () => {
    const params = writeDashboardState({ timeRange: "this_month" });
    expect(params.toString()).toBe("");
  });

  it("includes non-default time range", () => {
    const params = writeDashboardState({ timeRange: "last_3_months" });
    expect(params.get("range")).toBe("last_3_months");
  });
});

describe("writeAnomalyState", () => {
  it("omits default time range", () => {
    const params = writeAnomalyState({ timeRange: "this_month" });
    expect(params.toString()).toBe("");
  });

  it("includes time range and department prefilter", () => {
    const params = writeAnomalyState({
      timeRange: "last_3_months",
      departmentId: "eng",
    });
    expect(params.get("range")).toBe("last_3_months");
    expect(params.get("department_id")).toBe("eng");
  });

  it("includes severity when set", () => {
    const params = writeAnomalyState({
      timeRange: "this_month",
      severity: "high",
    });
    expect(params.get("severity")).toBe("high");
  });

  it("does not include undefined optional fields", () => {
    const params = writeAnomalyState({
      timeRange: "this_month",
      departmentId: undefined,
      severity: undefined,
    });
    expect(params.has("department_id")).toBe(false);
    expect(params.has("severity")).toBe(false);
  });
});

describe("writeDepartmentDetailState", () => {
  it("includes department id and source", () => {
    const params = writeDepartmentDetailState({
      departmentId: "sales",
      timeRange: "last_12_months",
      source: "anomalies",
      anomalyId: "a1",
    });
    expect(params.get("department_id")).toBe("sales");
    expect(params.get("range")).toBe("last_12_months");
    expect(params.get("source")).toBe("anomalies");
    expect(params.get("anomaly_id")).toBe("a1");
  });

  it("omits default time range", () => {
    const params = writeDepartmentDetailState({
      departmentId: "hr",
      timeRange: "this_month",
    });
    expect(params.has("range")).toBe(false);
  });
});

describe("route-state round-trip", () => {
  it("dashboard state read-write consistent", () => {
    const state = { timeRange: "last_3_months" as const };
    const params = writeDashboardState(state);
    const parsed = readDashboardState(params);
    expect(parsed).toEqual(state);
  });

  it("anomaly state read-write consistent", () => {
    const state = {
      timeRange: "last_12_months" as const,
      departmentId: "eng",
      severity: "high" as const,
    };
    const params = writeAnomalyState(state);
    const parsed = readAnomalyState(params);
    expect(parsed).toEqual(state);
  });

  it("department detail state read-write consistent", () => {
    const state = {
      departmentId: "sales",
      timeRange: "this_month" as const,
      source: "dashboard_ranking" as const,
      anomalyId: "a42",
    };
    const params = writeDepartmentDetailState(state);
    const parsed = readDepartmentDetailState(params);
    // source field matches
    expect(parsed.departmentId).toBe(state.departmentId);
    expect(parsed.timeRange).toBe(state.timeRange);
    expect(parsed.source).toBe(state.source);
    expect(parsed.anomalyId).toBe(state.anomalyId);
  });
});
