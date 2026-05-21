import type { TimeRangeKey } from "@/lib/navigation/time-range";
import type {
  DashboardSummary,
  DepartmentSummary,
  MonthlyTrend,
  ClaimTypeBreakdown,
  Anomaly,
} from "@/lib/api/types";

export type MetricCard = {
  label: string;
  value: number;
  delta?: number;
  clickable: boolean;
};

export type AttentionListItem = {
  id: string;
  departmentId: string;
  departmentName: string;
  severity: "high" | "medium" | "low";
  reason: string;
  changePct: number;
};

export type SummaryBrief = {
  headline: string;
  bullets: string[];
};

export type TrendSeries = {
  label: string;
  data: { month: string; value: number }[];
};

export type DepartmentPreviewItem = {
  id: string;
  name: string;
  totalSpend: number;
  changePct: number;
  attentionState: string | null;
};

export type DashboardCommandView = {
  snapshotId: string;
  snapshotLabel: string;
  timeRange: TimeRangeKey;
  summaryCards: {
    totalSpend: MetricCard;
    payrollSpend: MetricCard;
    claimsSpend: MetricCard;
    attentionCount: MetricCard;
  };
  topAttentionItems: AttentionListItem[];
  aiSummary: SummaryBrief;
  trendSeries: TrendSeries[];
  topDepartments: DepartmentPreviewItem[];
};

export const mapCommandView = (
  summary: DashboardSummary,
  departments: DepartmentSummary[],
  trends: MonthlyTrend[],
  claimTypes: ClaimTypeBreakdown[],
  anomalies: Anomaly[],
  timeRange: TimeRangeKey,
): DashboardCommandView => {
  const snapshotId = summary.last_updated;
  const snapshotLabel = `${summary.period.year}-${String(summary.period.month).padStart(2, "0")}`;

  return {
    snapshotId,
    snapshotLabel,
    timeRange,
    summaryCards: {
      totalSpend: {
        label: "Total Spend",
        value: summary.total_payroll + summary.total_claims,
        clickable: false,
      },
      payrollSpend: {
        label: "Payroll Spend",
        value: summary.total_payroll,
        clickable: false,
      },
      claimsSpend: {
        label: "Claims Spend",
        value: summary.total_claims,
        clickable: false,
      },
      attentionCount: {
        label: "Attention Count",
        value: summary.anomaly_count,
        clickable: true,
      },
    },
    topAttentionItems: anomalies.slice(0, 3).map((a) => ({
      id: a.id,
      departmentId: a.department_id,
      departmentName: a.department_name,
      severity: a.severity,
      reason: a.description,
      changePct: a.change_pct,
    })),
    aiSummary: {
      headline: `Spend overview for ${snapshotLabel}`,
      bullets: [
        `Total spend: $${((summary.total_payroll + summary.total_claims) / 1000).toFixed(0)}k across ${summary.department_count} departments`,
        `${summary.anomaly_count} departments show unusual spend patterns requiring review`,
        claimTypes.length > 0
          ? `Top claim type: ${claimTypes[0]?.type ?? "N/A"} at $${((claimTypes[0]?.amount ?? 0) / 1000).toFixed(0)}k`
          : "No claim data available",
      ],
    },
    trendSeries: [
      {
        label: "Total",
        data: trends.map((t) => ({ month: t.month, value: t.total })),
      },
      {
        label: "Payroll",
        data: trends.map((t) => ({ month: t.month, value: t.payroll })),
      },
      {
        label: "Claims",
        data: trends.map((t) => ({ month: t.month, value: t.claims })),
      },
    ],
    topDepartments: departments.slice(0, 5).map((d) => ({
      id: d.id,
      name: d.name,
      totalSpend: d.total_spend,
      changePct: d.change_pct,
      attentionState: anomalies.some((a) => a.department_id === d.id)
        ? anomalies.find((a) => a.department_id === d.id)!.severity
        : null,
    })),
  };
}
