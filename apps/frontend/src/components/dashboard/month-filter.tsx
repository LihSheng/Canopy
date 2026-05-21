"use client";

import { useRouter, useSearchParams } from "next/navigation";

export const MonthFilter = () => {
  const router = useRouter();
  const searchParams = useSearchParams();

  const now = new Date();
  const currentYear = now.getFullYear();
  const currentMonth = now.getMonth() + 1;

  const year = parseInt(searchParams.get("year") || String(currentYear), 10);
  const month = parseInt(searchParams.get("month") || String(currentMonth), 10);

  const months = [
    "Jan", "Feb", "Mar", "Apr", "May", "Jun",
    "Jul", "Aug", "Sep", "Oct", "Nov", "Dec",
  ];

  const years = Array.from({ length: 5 }, (_, i) => currentYear - i);

  function navigate(y: number, m: number) {
    const params = new URLSearchParams(searchParams.toString());
    params.set("year", String(y));
    params.set("month", String(m));
    router.push(`/dashboard?${params.toString()}`);
  }

  return (
    <div className="flex items-center gap-3">
      <select
        value={year}
        onChange={(e) => navigate(parseInt(e.target.value), month)}
        className="h-9 rounded-lg border border-zinc-200 bg-white px-3 text-sm text-zinc-700 focus:border-zinc-900 focus:outline-none"
      >
        {years.map((y) => (
          <option key={y} value={y}>
            {y}
          </option>
        ))}
      </select>
      <div className="flex rounded-lg border border-zinc-200 bg-white p-0.5">
        {months.map((label, index) => {
          const m = index + 1;
          const isActive = m === month;
          return (
            <button
              key={label}
              onClick={() => navigate(year, m)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                isActive
                  ? "bg-zinc-900 text-white"
                  : "text-zinc-500 hover:text-zinc-900"
              }`}
            >
              {label}
            </button>
          );
        })}
      </div>
    </div>
  );
}
