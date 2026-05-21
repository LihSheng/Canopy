import type { MonthlyTrend, DepartmentSummary, ClaimTypeBreakdown } from "@/lib/api/types";

export interface TrendChartData {
  month: string;
  Payroll: number;
  Claims: number;
  Total: number;
}

export const mapToTrendChart = (trends: MonthlyTrend[]): TrendChartData[] => {
  return trends.map((t) => ({
    month: t.month,
    Payroll: t.payroll,
    Claims: t.claims,
    Total: t.total,
  }));
}

export const mapToDepartmentRanking = (departments: DepartmentSummary[]): DepartmentSummary[] => {
  return [...departments].sort((a, b) => b.total_spend - a.total_spend);
}

export const mapToClaimTypeBreakdown = (breakdowns: ClaimTypeBreakdown[]): ClaimTypeBreakdown[] => {
  return [...breakdowns].sort((a, b) => b.amount - a.amount);
}
