const currencyFormatter = new Intl.NumberFormat("en-US", {
  style: "currency",
  currency: "USD",
  minimumFractionDigits: 0,
  maximumFractionDigits: 0,
});

export function formatCurrency(value: number): string {
  return currencyFormatter.format(value);
}

export function formatPercent(value: number): string {
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export function getChangeColor(value: number): string {
  if (value > 5) return "text-red-600";
  if (value < -5) return "text-emerald-600";
  return "text-zinc-500";
}

export function getChangeBgColor(value: number): string {
  if (value > 5) return "bg-red-50 text-red-700";
  if (value < -5) return "bg-emerald-50 text-emerald-700";
  return "bg-zinc-50 text-zinc-600";
}

export function getSeverityColor(severity: "low" | "medium" | "high"): string {
  switch (severity) {
    case "high":
      return "bg-red-50 text-red-700 border-red-200";
    case "medium":
      return "bg-amber-50 text-amber-700 border-amber-200";
    case "low":
      return "bg-blue-50 text-blue-700 border-blue-200";
  }
}
