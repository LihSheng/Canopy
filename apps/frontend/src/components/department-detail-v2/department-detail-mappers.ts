import type { TimeRangeKey } from "@/lib/navigation/time-range";
import type {
  DepartmentDetail,
  EmployeeContribution,
  ClaimDetail,
  MonthlyTrend,
  Anomaly,
} from "@/lib/api/types";

export type SummaryBrief = {
  headline: string;
  bullets: string[];
};

export type TrendSeries = {
  label: string;
  data: { month: string; value: number }[];
};

export type ContributorItem = {
  id: string;
  name: string;
  total: number;
};

export type DepartmentDetailView = {
  snapshotId: string;
  department: { id: string; name: string; attentionState: string | null };
  timeRange: TimeRangeKey;
  summary: { totalSpend: number; changePercent: number };
  trend: TrendSeries[];
  aiSummary: SummaryBrief;
  topEmployees: ContributorItem[];
  topClaimTypes: ContributorItem[];
};

export function mapDepartmentDetailView(
  department: DepartmentDetail,
  employees: EmployeeContribution[],
  claims: ClaimDetail[],
  trends: MonthlyTrend[],
  anomalies: Anomaly[],
  timeRange: TimeRangeKey,
): DepartmentDetailView {
  const snapshotId = `${new Date().toISOString().slice(0, 7)}`;

  const severityOrder = { high: 3, medium: 2, low: 1 } as const;
  const deptAnomalies = anomalies.filter((a) => a.department_id === department.id);
  const topSeverity = deptAnomalies.length > 0
    ? deptAnomalies.reduce((best, a) =>
        severityOrder[a.severity] > severityOrder[best.severity] ? a : best,
      )
    : null;
  const attentionState = topSeverity?.severity ?? null;

  const topEmployees = [...employees]
    .sort((a, b) => b.total - a.total)
    .slice(0, 5)
    .map((e) => ({
      id: e.id,
      name: e.name,
      total: e.total,
    }));

  const claimTypeMap = new Map<string, number>();
  for (const c of claims) {
    claimTypeMap.set(c.type, (claimTypeMap.get(c.type) ?? 0) + c.amount);
  }
  const topClaimTypes = [...claimTypeMap.entries()]
    .sort(([, a], [, b]) => b - a)
    .slice(0, 5)
    .map(([type, amount], i) => ({
      id: `ct-${i}`,
      name: type,
      total: amount,
    }));

  const trend: TrendSeries[] = trends.length > 0
    ? [
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
      ]
    : [];

  const topClaimTypeName = topClaimTypes.length > 0 ? topClaimTypes[0].name : "N/A";
  const topClaimTypeAmount = topClaimTypes.length > 0 ? topClaimTypes[0].total : 0;

  const aiSummary: SummaryBrief = {
    headline: `${department.name} spent ${formatCompact(department.total_spend)} this period${attentionState ? `, triggering a ${attentionState} attention state` : "."}`,
    bullets: [
      `${topEmployees.length > 0 ? topEmployees[0].name : "No employees"} is the highest spender at ${topEmployees.length > 0 ? formatCompact(topEmployees[0].total) : "$0"}`,
      `${topClaimTypes.length > 0 ? topClaimTypeName : "No claims"} leads claim types at ${formatCompact(topClaimTypeAmount)}`,
      `Change from previous period: ${department.change_pct >= 0 ? "+" : ""}${department.change_pct.toFixed(1)}% across ${department.employee_count} employees`,
    ],
  };

  return {
    snapshotId,
    department: { id: department.id, name: department.name, attentionState },
    timeRange,
    summary: {
      totalSpend: department.total_spend,
      changePercent: department.change_pct,
    },
    trend,
    aiSummary,
    topEmployees,
    topClaimTypes,
  };
}

function formatCompact(value: number): string {
  if (value >= 1_000_000) return `$${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `$${(value / 1_000).toFixed(0)}k`;
  return `$${value.toFixed(0)}`;
}
