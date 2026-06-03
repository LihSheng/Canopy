import { describe, expect, it, vi, beforeEach } from "vitest";
import { request } from "@/lib/api/client";

vi.mock("@/lib/api/client", () => ({
  request: vi.fn(),
  API_BASE: "http://localhost:8005",
}));

import {
  fetchCommandView,
  fetchSummary,
  fetchDepartments,
  fetchMonthlyTrends,
  fetchClaimTypeBreakdown,
  fetchAnomalies,
  fetchDepartmentDetail,
  fetchEmployeeContributions,
  fetchClaimDetails,
  fetchRefreshStatus,
  triggerRefresh,
} from "@/lib/api/dashboard";

const mockRequest = vi.mocked(request);

describe("dashboard API", () => {
  beforeEach(() => {
    mockRequest.mockReset();
  });

  describe("fetchCommandView", () => {
    it("calls /api/dashboard/command-view", async () => {
      mockRequest.mockResolvedValue({ summary: {} });
      await fetchCommandView();
      expect(mockRequest).toHaveBeenCalledWith("/api/dashboard/command-view");
    });
  });

  describe("fetchSummary", () => {
    it("calls /api/dashboard/summary", async () => {
      mockRequest.mockResolvedValue({ total_payroll: 1000 });
      const result = await fetchSummary();
      expect(mockRequest).toHaveBeenCalledWith("/api/dashboard/summary");
      expect(result).toEqual({ total_payroll: 1000 });
    });
  });

  describe("fetchDepartments", () => {
    it("calls /api/departments without params", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchDepartments();
      expect(mockRequest).toHaveBeenCalledWith("/api/departments");
    });

    it("appends query string when params given", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchDepartments({ year: 2026, month: 5 });
      expect(mockRequest).toHaveBeenCalledWith("/api/departments?year=2026&month=5");
    });
  });

  describe("fetchMonthlyTrends", () => {
    it("calls /api/dashboard/trends without params", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchMonthlyTrends();
      expect(mockRequest).toHaveBeenCalledWith("/api/dashboard/trends");
    });

    it("appends query string when params given", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchMonthlyTrends({ year: 2026, month: 5 });
      expect(mockRequest).toHaveBeenCalledWith("/api/dashboard/trends?year=2026&month=5");
    });
  });

  describe("fetchClaimTypeBreakdown", () => {
    it("calls /api/dashboard/claim-types without params", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchClaimTypeBreakdown();
      expect(mockRequest).toHaveBeenCalledWith("/api/dashboard/claim-types");
    });

    it("appends query string when params given", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchClaimTypeBreakdown({ year: 2026, month: 5 });
      expect(mockRequest).toHaveBeenCalledWith("/api/dashboard/claim-types?year=2026&month=5");
    });
  });

  describe("fetchAnomalies", () => {
    it("calls /api/anomalies", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchAnomalies();
      expect(mockRequest).toHaveBeenCalledWith("/api/anomalies");
    });
  });

  describe("fetchDepartmentDetail", () => {
    it("calls /api/departments/:id without params", async () => {
      mockRequest.mockResolvedValue({ id: "dept-1" });
      await fetchDepartmentDetail("dept-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/departments/dept-1");
    });

    it("appends query string when params given", async () => {
      mockRequest.mockResolvedValue({ id: "dept-1" });
      await fetchDepartmentDetail("dept-1", { year: 2026, month: 5 });
      expect(mockRequest).toHaveBeenCalledWith("/api/departments/dept-1?year=2026&month=5");
    });
  });

  describe("fetchEmployeeContributions", () => {
    it("calls /api/departments/:id/employees without params", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchEmployeeContributions("dept-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/departments/dept-1/employees");
    });

    it("appends query string when params given", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchEmployeeContributions("dept-1", { year: 2026, month: 5 });
      expect(mockRequest).toHaveBeenCalledWith("/api/departments/dept-1/employees?year=2026&month=5");
    });
  });

  describe("fetchClaimDetails", () => {
    it("calls /api/claims with no filters", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchClaimDetails();
      expect(mockRequest).toHaveBeenCalledWith("/api/claims");
    });

    it("appends department_id when provided", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchClaimDetails("dept-1");
      expect(mockRequest).toHaveBeenCalledWith("/api/claims?department_id=dept-1");
    });

    it("appends all params when department and month provided", async () => {
      mockRequest.mockResolvedValue([]);
      await fetchClaimDetails("dept-1", { year: 2026, month: 5 });
      expect(mockRequest).toHaveBeenCalledWith("/api/claims?department_id=dept-1&year=2026&month=5");
    });
  });

  describe("fetchRefreshStatus", () => {
    it("calls /api/refresh/current", async () => {
      mockRequest.mockResolvedValue({ status: "idle" });
      const result = await fetchRefreshStatus();
      expect(mockRequest).toHaveBeenCalledWith("/api/refresh/current");
      expect(result).toEqual({ status: "idle" });
    });
  });

  describe("triggerRefresh", () => {
    it("calls /api/refresh with POST", async () => {
      mockRequest.mockResolvedValue({ accepted: true });
      const result = await triggerRefresh();
      expect(mockRequest).toHaveBeenCalledWith("/api/refresh", { method: "POST" });
      expect(result).toEqual({ accepted: true });
    });
  });
});
