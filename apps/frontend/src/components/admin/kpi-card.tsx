"use client";

type Variant = "normal" | "warning" | "danger";

interface KpiCardProps {
  label: string;
  value: string;
  trend?: "up" | "down" | "stable";
  variant?: Variant;
}

const VARIANT_STYLES: Record<Variant, string> = {
  normal: "bg-white",
  warning: "bg-amber-50 border-amber-200",
  danger: "bg-red-50 border-red-200",
};

const TREND_ICONS: Record<string, string> = {
  up: "\u2191",
  down: "\u2193",
  stable: "\u2192",
};

const TREND_COLORS: Record<string, string> = {
  up: "text-red-600",
  down: "text-green-600",
  stable: "text-zinc-400",
};

export const KpiCard = ({ label, value, trend, variant = "normal" }: KpiCardProps) => {
  return (
    <div
      className={`rounded-lg border px-4 py-3 ${VARIANT_STYLES[variant]}`}
    >
      <p className="text-xs font-medium uppercase tracking-wider text-zinc-500">
        {label}
      </p>
      <p className="mt-1 flex items-baseline gap-1.5 text-2xl font-bold text-zinc-900">
        {value}
        {trend && (
          <span className={`text-sm ${TREND_COLORS[trend]}`}>
            {TREND_ICONS[trend]}
          </span>
        )}
      </p>
    </div>
  );
};
