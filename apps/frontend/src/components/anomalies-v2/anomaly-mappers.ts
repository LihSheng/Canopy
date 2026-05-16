import type { Anomaly } from "@/lib/api/types";

export type AnomalyListItem = {
  id: string;
  departmentId: string;
  departmentName: string;
  severity: "high" | "medium" | "low";
  reason: string;
  changePct: number;
  period: string;
};

export type AnomalyGroup = {
  severity: "high" | "medium" | "low";
  count: number;
  items: AnomalyListItem[];
};

export type AnomalyListView = {
  snapshotId: string;
  groups: AnomalyGroup[];
};

export function mapAnomalyListView(anomalies: Anomaly[]): AnomalyListView {
  const map = new Map<string, AnomalyListItem[]>();

  for (const a of anomalies) {
    const item: AnomalyListItem = {
      id: a.id,
      departmentId: a.department_id,
      departmentName: a.department_name,
      severity: a.severity,
      reason: a.description,
      changePct: a.change_pct,
      period: a.period,
    };
    const existing = map.get(a.severity);
    if (existing) {
      existing.push(item);
    } else {
      map.set(a.severity, [item]);
    }
  }

  const groups: AnomalyGroup[] = (["high", "medium", "low"] as const)
    .filter((s) => map.has(s))
    .map((severity) => ({
      severity,
      count: map.get(severity)!.length,
      items: map.get(severity)!,
    }));

  return {
    snapshotId: anomalies.length > 0 ? anomalies[0].period : "",
    groups,
  };
}

export function filterAnomalies(
  items: AnomalyListItem[],
  severity: "high" | "medium" | "low" | null,
  departmentId?: string,
): AnomalyListItem[] {
  let filtered = items;

  if (severity) {
    filtered = filtered.filter((a) => a.severity === severity);
  }

  if (departmentId) {
    filtered = filtered.filter((a) => a.departmentId === departmentId);
  }

  return filtered;
}
