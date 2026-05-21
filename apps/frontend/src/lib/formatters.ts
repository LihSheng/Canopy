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
}
