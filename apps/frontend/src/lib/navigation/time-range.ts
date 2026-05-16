export type TimeRangeKey = "this_month" | "last_3_months" | "last_12_months";

export const DEFAULT_TIME_RANGE: TimeRangeKey = "this_month";

export const TIME_RANGE_LABELS: Record<TimeRangeKey, string> = {
  this_month: "This month",
  last_3_months: "Last 3 months",
  last_12_months: "Last 12 months",
};

export function parseTimeRange(raw: string | null | undefined): TimeRangeKey {
  if (raw === "last_3_months" || raw === "last_12_months") return raw;
  return DEFAULT_TIME_RANGE;
}
