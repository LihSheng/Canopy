import type { DepartmentSummary, Anomaly } from "@/lib/api/types";

export type DepartmentRankingItem = {
  id: string;
  name: string;
  totalSpend: number;
  payrollSpend: number;
  claimsSpend: number;
  changePct: number;
  attentionState: "high" | "medium" | "low" | null;
};

export type SortKey = "attention" | "total_spend" | "change_percent";

export const SORT_LABELS: Record<SortKey, string> = {
  attention: "Attention",
  total_spend: "Total spend",
  change_percent: "Change %",
};

const ATTENTION_SEVERITY: Record<string, number> = {
  high: 0,
  medium: 1,
  low: 2,
};

export const attachAttentionState = (
  departments: DepartmentSummary[],
  anomalies: Anomaly[],
): DepartmentRankingItem[] => {
  const anomalyMap = new Map<string, "high" | "medium" | "low">();
  for (const a of anomalies) {
    const existing = anomalyMap.get(a.department_id);
    if (!existing || ATTENTION_SEVERITY[a.severity] < ATTENTION_SEVERITY[existing]) {
      anomalyMap.set(a.department_id, a.severity);
    }
  }

  return departments.map((d) => ({
    id: d.id,
    name: d.name,
    totalSpend: d.total_spend,
    payrollSpend: d.payroll_spend,
    claimsSpend: d.claims_spend,
    changePct: d.change_pct,
    attentionState: anomalyMap.get(d.id) ?? null,
  }));
}

export const sortItems = (items: DepartmentRankingItem[], sort: SortKey): DepartmentRankingItem[] => {
  const sorted = [...items];

  switch (sort) {
    case "attention":
      sorted.sort((a, b) => {
        const aSev = a.attentionState ? ATTENTION_SEVERITY[a.attentionState] : 99;
        const bSev = b.attentionState ? ATTENTION_SEVERITY[b.attentionState] : 99;
        return aSev - bSev;
      });
      break;
    case "total_spend":
      sorted.sort((a, b) => b.totalSpend - a.totalSpend);
      break;
    case "change_percent":
      sorted.sort((a, b) => Math.abs(b.changePct) - Math.abs(a.changePct));
      break;
  }

  return sorted;
}

export const filterDepartments = (
  items: DepartmentRankingItem[],
  search: string,
  attentionOnly: boolean,
): DepartmentRankingItem[] => {
  let filtered = items;

  if (search.trim()) {
    const lower = search.toLowerCase().trim();
    filtered = filtered.filter((d) => d.name.toLowerCase().includes(lower));
  }

  if (attentionOnly) {
    filtered = filtered.filter((d) => d.attentionState !== null);
  }

  return filtered;
}
