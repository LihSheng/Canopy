import { describe, expect, it } from "vitest";
import {
  buildDashboardToAnomaliesLink,
  buildDashboardToAnomaliesWithSeverityLink,
  buildDashboardToDepartmentDetailLink,
} from "@/lib/navigation/dashboard-links";
import {
  buildAnomalyToDepartmentDetailLink,
} from "@/lib/navigation/anomaly-links";
import {
  buildDepartmentToAnomaliesLink,
} from "@/lib/navigation/department-links";

describe("dashboard-links", () => {
  describe("buildDashboardToAnomaliesLink", () => {
    it("builds link with default time range (no query)", () => {
      const link = buildDashboardToAnomaliesLink("this_month");
      expect(link).toBe("/dashboard/anomalies?");
    });

    it("builds link with custom time range", () => {
      const link = buildDashboardToAnomaliesLink("last_3_months");
      expect(link).toContain("/dashboard/anomalies");
      expect(link).toContain("range=last_3_months");
    });
  });

  describe("buildDashboardToAnomaliesWithSeverityLink", () => {
    it("builds link with severity filter", () => {
      const link = buildDashboardToAnomaliesWithSeverityLink(
        "last_3_months",
        "high",
      );
      expect(link).toContain("/dashboard/anomalies");
      expect(link).toContain("range=last_3_months");
      expect(link).toContain("severity=high");
    });
  });

  describe("buildDashboardToDepartmentDetailLink", () => {
    it("builds link for dashboard attention source", () => {
      const link = buildDashboardToDepartmentDetailLink(
        "eng",
        "this_month",
        "dashboard_attention",
      );
      expect(link).toContain("/dashboard/departments/eng");
      expect(link).toContain("source=dashboard_attention");
    });

    it("builds link for dashboard ranking source", () => {
      const link = buildDashboardToDepartmentDetailLink(
        "sales",
        "last_12_months",
        "dashboard_ranking",
      );
      expect(link).toContain("/dashboard/departments/sales");
      expect(link).toContain("source=dashboard_ranking");
      expect(link).toContain("range=last_12_months");
    });

    it("encodes department id with special chars", () => {
      const link = buildDashboardToDepartmentDetailLink(
        "HR & Finance",
        "this_month",
        "dashboard_attention",
      );
      expect(link).toContain("/dashboard/departments/HR%20%26%20Finance");
    });
  });
});

describe("anomaly-links", () => {
  describe("buildAnomalyToDepartmentDetailLink", () => {
    it("builds link with anomaly context", () => {
      const link = buildAnomalyToDepartmentDetailLink(
        "eng",
        "last_3_months",
        "a1",
      );
      expect(link).toContain("/dashboard/departments/eng");
      expect(link).toContain("source=anomalies");
      expect(link).toContain("anomaly_id=a1");
      expect(link).toContain("range=last_3_months");
    });

    it("builds link without optional anomaly id", () => {
      const link = buildAnomalyToDepartmentDetailLink(
        "hr",
        "this_month",
      );
      expect(link).toContain("/dashboard/departments/hr");
      expect(link).toContain("source=anomalies");
      expect(link).not.toContain("anomaly_id");
    });
  });
});

describe("department-links", () => {
  describe("buildDepartmentToAnomaliesLink", () => {
    it("carries department id and time range to anomalies page", () => {
      const link = buildDepartmentToAnomaliesLink("sales", "last_12_months");
      expect(link).toContain("/dashboard/anomalies");
      expect(link).toContain("department_id=sales");
      expect(link).toContain("range=last_12_months");
    });

    it("works with default time range", () => {
      const link = buildDepartmentToAnomaliesLink("eng", "this_month");
      expect(link).toContain("/dashboard/anomalies");
      expect(link).toContain("department_id=eng");
    });
  });
});
