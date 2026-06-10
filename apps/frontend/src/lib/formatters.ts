import { DEFAULT_LOCALE, DEFAULT_CURRENCY, type Severity } from "@/lib/constants";

const currencyFormatter = new Intl.NumberFormat(DEFAULT_LOCALE, {
  style: "currency",
  currency: DEFAULT_CURRENCY,
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export const formatCurrency = (value: number): string => {
  return currencyFormatter.format(value);
}

export const formatPercent = (value: number): string => {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export const getChangeColor = (value: number): string => {
  if (value > 5) return "text-red-600";
  if (value < -5) return "text-emerald-600";
  return "text-zinc-500";
}

export const getChangeBgColor = (value: number): string => {
  if (value > 5) return "bg-red-50 text-red-700";
  if (value < -5) return "bg-emerald-50 text-emerald-700";
  return "bg-zinc-50 text-zinc-600";
}

export const getSeverityColor = (severity: Severity): string => {
  switch (severity) {
    case "high":
      return "bg-red-50 text-red-700 border-red-200";
    case "medium":
      return "bg-amber-50 text-amber-700 border-amber-200";
    case "low":
      return "bg-blue-50 text-blue-700 border-blue-200";
  }
  return "bg-zinc-50 text-zinc-600 border-zinc-200";
};

// ── Entity property format hints ───────────────────────────────────────

const number2dpFormatter = new Intl.NumberFormat(DEFAULT_LOCALE, {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

const dateShortFormatter = new Intl.DateTimeFormat(DEFAULT_LOCALE, {
  year: "numeric",
  month: "short",
  day: "numeric",
});

const dateLongFormatter = new Intl.DateTimeFormat(DEFAULT_LOCALE, {
  year: "numeric",
  month: "long",
  day: "numeric",
  weekday: "long",
});

/**
 * Format a value according to an optional format hint.
 * Used when displaying materialized entity rows.
 */
export const formatValue = (value: unknown, formatHint?: string): string => {
  if (value === null || value === undefined) return "—";

  switch (formatHint) {
    case "currency":
      if (typeof value === "number") return formatCurrency(value);
      break;
    case "percentage":
      if (typeof value === "number") return formatPercent(value);
      break;
    case "number_2dp":
      if (typeof value === "number") return number2dpFormatter.format(value);
      break;
    case "date_short":
      if (value instanceof Date || typeof value === "string") {
        return dateShortFormatter.format(new Date(value as string));
      }
      break;
    case "date_long":
      if (value instanceof Date || typeof value === "string") {
        return dateLongFormatter.format(new Date(value as string));
      }
      break;
    case "boolean_yesno":
      return value ? "Yes" : "No";
  }

  return String(value);
};
