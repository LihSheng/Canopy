"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { AnalyticsHeader } from "@/components/analytics-shell/analytics-header";
import { AnalyticsBreadcrumb } from "@/components/analytics-shell/analytics-breadcrumb";
import { ErrorState } from "@/components/shared/error-state";
import { EmptyState } from "@/components/shared/empty-state";
import { DepartmentRankedRow } from "./department-ranked-row";
import { DepartmentsFilterBar } from "./departments-filter-bar";
import {
  attachAttentionState,
  sortItems,
  filterDepartments,
} from "./department-list-mappers";
import type { SortKey, DepartmentRankingItem } from "./department-list-mappers";
import { TIME_RANGE_LABELS, type TimeRangeKey } from "@/lib/navigation/time-range";
import { fetchDepartments, fetchAnomalies } from "@/lib/api/dashboard";

type DataState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; items: DepartmentRankingItem[] };

export function DepartmentsPage() {
  const [search, setSearch] = useState("");
  const [attentionOnly, setAttentionOnly] = useState(false);
  const [timeRange, setTimeRange] = useState<TimeRangeKey>("this_month");
  const [activeSort, setActiveSort] = useState<SortKey>("attention");
  const [data, setData] = useState<DataState>({ status: "loading" });

  const load = useCallback(async () => {
    setData({ status: "loading" });
    try {
      const [departments, anomalies] = await Promise.all([
        fetchDepartments(),
        fetchAnomalies(),
      ]);
      const ranked = attachAttentionState(departments, anomalies);
      setData({ status: "success", items: ranked });
    } catch (err) {
      setData({
        status: "error",
        message: err instanceof Error ? err.message : "Failed to load departments",
      });
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial data fetch
    load();
  }, [load]);

  const filteredAndSorted = useMemo(() => {
    if (data.status !== "success") return [];
    const filtered = filterDepartments(data.items, search, attentionOnly);
    return sortItems(filtered, activeSort);
  }, [data, search, attentionOnly, activeSort]);

  const contextLabel = TIME_RANGE_LABELS[timeRange];

  if (data.status === "error") {
    return (
      <>
        <AnalyticsHeader title="Departments" />
        <AnalyticsBreadcrumb
          items={[
            { label: "Dashboard", href: "/dashboard" },
            { label: "Departments" },
          ]}
        />
        <div className="p-6">
          <ErrorState message={data.message} onRetry={load} />
        </div>
      </>
    );
  }

  const loading = data.status === "loading";

  return (
    <div className="flex flex-col h-full overflow-auto">
      <AnalyticsHeader
        title="Departments"
        contextText={`${contextLabel}${!loading && data.status === "success"
          ? ` \u00b7 ${filteredAndSorted.length} department${filteredAndSorted.length !== 1 ? "s" : ""}`
          : ""
        }`}
      />
      <AnalyticsBreadcrumb
        items={[
          { label: "Dashboard", href: "/dashboard" },
          { label: "Departments" },
        ]}
      />

      <div className="flex-1 overflow-auto p-6">
        <div className="mb-6">
          <DepartmentsFilterBar
            search={search}
            attentionOnly={attentionOnly}
            timeRange={timeRange}
            activeSort={activeSort}
            onSearchChange={setSearch}
            onAttentionOnlyChange={setAttentionOnly}
            onTimeRangeChange={setTimeRange}
            onSortChange={setActiveSort}
          />
        </div>

        {loading && (
          <div className="rounded-xl border border-zinc-200 bg-white">
            <div className="divide-y divide-zinc-100">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center gap-4 px-4 py-3">
                  <div className="flex-1">
                    <div className="h-3.5 w-32 animate-pulse rounded bg-zinc-100" />
                  </div>
                  <div className="h-3.5 w-20 animate-pulse rounded bg-zinc-100" />
                  <div className="h-5 w-14 animate-pulse rounded-full bg-zinc-100" />
                </div>
              ))}
            </div>
          </div>
        )}

        {data.status === "success" && data.items.length === 0 && (
          <EmptyState
            title="No departments"
            description="Department data will appear after the first sync completes."
          />
        )}

        {data.status === "success" && data.items.length > 0 && filteredAndSorted.length === 0 && (
          <div className="rounded-xl border border-zinc-200 bg-white px-5 py-10 text-center">
            <p className="text-sm text-zinc-500">No departments match your filters</p>
            <button
              onClick={() => {
                setSearch("");
                setAttentionOnly(false);
              }}
              className="mt-2 text-xs font-medium text-zinc-500 underline hover:text-zinc-900"
            >
              Clear all filters
            </button>
          </div>
        )}

        {data.status === "success" && filteredAndSorted.length > 0 && (
          <div className="rounded-xl border border-zinc-200 bg-white">
            <div className="divide-y divide-zinc-100">
              {filteredAndSorted.map((item) => (
                <DepartmentRankedRow
                  key={item.id}
                  item={item}
                  timeRange={timeRange}
                />
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
